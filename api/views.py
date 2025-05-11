from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action, api_view, permission_classes
from .models import GodzinyPracy, WniosekUrlopowy, Profile, User
from .serializers import UserSerializer, GodzinyPracySerializer, WniosekUrlopowySerializer, ProfileSerializer
import io
import xlsxwriter
from datetime import datetime
from django.http import HttpResponse, JsonResponse
from reportlab.pdfgen import canvas
from django.core.mail import send_mail
from rest_framework.exceptions import PermissionDenied

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        raise PermissionDenied("Nie można tworzyć użytkowników przez ten endpoint.")

    def update(self, request, *args, **kwargs):
        user = request.user
        instance = self.get_object()

        if user.role == 'admin':
            return super().update(request, *args, **kwargs)

        if user.role == 'kierownik':
            if instance.role != 'pracownik':
                raise PermissionDenied("Kierownik może edytować tylko pracowników.")
            return super().update(request, *args, **kwargs)

        raise PermissionDenied("Nie masz uprawnień do edycji użytkownika.")

    def partial_update(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        return Response(UserSerializer(request.user, context={'request': request}).data)

    @action(detail=True, methods=['patch'], permission_classes=[IsAuthenticated])
    def assign_department(self, request, pk=None):
        current_user = request.user
        user_to_edit = self.get_object()

        if current_user.role == 'admin' or (current_user.role == 'kierownik' and user_to_edit.role == 'pracownik'):
            dzial = request.data.get('dzial')
            if not dzial:
                return Response({'detail': 'Pole "dzial" jest wymagane.'}, status=status.HTTP_400_BAD_REQUEST)

            user_to_edit.dzial = dzial
            user_to_edit.save()
            return Response({'detail': f'Dział "{dzial}" został przypisany użytkownikowi {user_to_edit.username}.'})

        raise PermissionDenied("Nie masz uprawnień do przypisania działu temu użytkownikowi.")


class GodzinyPracyViewSet(viewsets.ModelViewSet):
    queryset = GodzinyPracy.objects.all()
    serializer_class = GodzinyPracySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.role == 'admin':
            return GodzinyPracy.objects.all()
        elif self.request.user.role == 'kierownik':
            return GodzinyPracy.objects.filter(user__dzial=self.request.user.dzial)
        return GodzinyPracy.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        instance = serializer.save()
        if instance.zatwierdzone:
            wyslij_powiadomienie_email(instance.user, "Twoje godziny pracy zostały zatwierdzone.")


class WniosekUrlopowyViewSet(viewsets.ModelViewSet):
    queryset = WniosekUrlopowy.objects.all().order_by('-data_utworzenia')
    serializer_class = WniosekUrlopowySerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(pracownik=self.request.user)

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return WniosekUrlopowy.objects.all()
        return WniosekUrlopowy.objects.filter(pracownik=user)


class GrafikViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        user = request.user
        rok = request.query_params.get('rok')
        miesiac = request.query_params.get('miesiac')

        if not rok or not miesiac:
            return Response({"detail": "Musisz podać 'rok' i 'miesiac' jako query params."}, status=400)

        try:
            rok = int(rok)
            miesiac = int(miesiac)
        except ValueError:
            return Response({"detail": "Rok i miesiąc muszą być liczbami całkowitymi."}, status=400)

        godziny = GodzinyPracy.objects.filter(user=user, rozpoczecie__year=rok, rozpoczecie__month=miesiac)

        urlopy = WniosekUrlopowy.objects.filter(pracownik=user)
        urlopy_w_miesiacu = []

        for urlop in urlopy:
            for dzien in urlop.wybrane_dni:
                try:
                    data = datetime.strptime(dzien, "%Y-%m-%d")
                    if data.year == rok and data.month == miesiac:
                        urlopy_w_miesiacu.append(urlop)
                        break
                except ValueError:
                    continue

        return Response({
            "godziny_pracy": GodzinyPracySerializer(godziny, many=True).data,
            "urlopy": WniosekUrlopowySerializer(urlopy_w_miesiacu, many=True).data,
            "suma_godzin": sum([g.czas_pracy() for g in godziny]),
            "dzial": user.dzial if hasattr(user, "dzial") else None,
            "username": user.username,
        })


def parse_month_param(request):
    month_str = request.GET.get('month')
    if not month_str:
        return None, JsonResponse({'error': 'Brak parametru "month" w formacie YYYY-MM.'}, status=400)
    try:
        return datetime.strptime(month_str, '%Y-%m'), None
    except ValueError:
        return None, JsonResponse({'error': 'Nieprawidłowy format "month". Użyj YYYY-MM.'}, status=400)


def get_target_user(request):
    user_id = request.GET.get("user_id")

    if not user_id:
        return request.user, None

    if request.user.role not in ["admin", "kierownik"]:
        return None, JsonResponse({"error": "Nie masz uprawnień do przeglądania danych innych użytkowników."},
                                  status=403)

    try:
        target_user = User.objects.get(id=user_id)
        return target_user, None
    except User.DoesNotExist:
        return None, JsonResponse({"error": "Podany użytkownik nie istnieje."}, status=404)


def eksport_excel(request):
    month_date, err = parse_month_param(request)
    if err:
        return err

    target_user, err = get_target_user(request)
    if err:
        return err

    # Zakres miesiąca
    start = month_date.replace(day=1)
    end = (start.replace(month=start.month % 12 + 1,
                         year=start.year + (start.month // 12))) if start.month != 12 else start.replace(
        year=start.year + 1, month=1)

    godziny = GodzinyPracy.objects.filter(user=target_user, rozpoczecie__gte=start, rozpoczecie__lt=end)

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet("Grafik")

    worksheet.write(0, 0, "Data rozpoczęcia")
    worksheet.write(0, 1, "Data zakończenia")
    worksheet.write(0, 2, "Zatwierdzone")

    for idx, g in enumerate(godziny, start=1):
        worksheet.write(idx, 0, str(g.rozpoczecie))
        worksheet.write(idx, 1, str(g.zakonczenie))
        worksheet.write(idx, 2, "Tak" if g.zatwierdzone else "Nie")

    workbook.close()
    output.seek(0)

    filename = f'grafik_{target_user.username}_{month_date.strftime("%Y_%m")}.xlsx'
    response = HttpResponse(output, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def eksport_pdf(request):
    month_date, err = parse_month_param(request)
    if err:
        return err

    target_user, err = get_target_user(request)
    if err:
        return err

    start = month_date.replace(day=1)
    end = (start.replace(month=start.month % 12 + 1,
                         year=start.year + (start.month // 12))) if start.month != 12 else start.replace(
        year=start.year + 1, month=1)

    godziny = GodzinyPracy.objects.filter(user=target_user, rozpoczecie__gte=start, rozpoczecie__lt=end)

    response = HttpResponse(content_type='application/pdf')
    response[
        'Content-Disposition'] = f'attachment; filename="grafik_{target_user.username}_{month_date.strftime("%Y_%m")}.pdf"'

    p = canvas.Canvas(response)
    p.setFont("Helvetica", 12)
    p.drawString(100, 800, f"Godziny Pracy – {target_user.username} – {month_date.strftime('%B %Y')}")

    y = 780
    for g in godziny:
        p.drawString(100, y,
                     f"{g.rozpoczecie.strftime('%Y-%m-%d %H:%M')} – {g.zakonczenie.strftime('%Y-%m-%d %H:%M')} ({'zatwierdzone' if g.zatwierdzone else 'oczekujące'})")
        y -= 20
        if y < 50:
            p.showPage()
            y = 800

    p.showPage()
    p.save()
    return response


def wyslij_powiadomienie_email(user, wiadomosc):
    send_mail(
        subject='Powiadomienie systemowe',
        message=wiadomosc,
        from_email='admin@twojadomena.pl',
        recipient_list=[user.email],
        fail_silently=False,
    )


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_profile_api(request):
    user = request.user
    profile, _ = Profile.objects.get_or_create(user=user)

    if request.method == 'GET':
        serializer = ProfileSerializer(profile)
        return Response(serializer.data)

    elif request.method == 'PUT':
        request.data.pop('dzial', None)
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
