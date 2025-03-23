from django.contrib.auth import get_user_model
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, DjangoModelPermissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.decorators import action
from .models import GodzinyPracy, WniosekUrlopowy
from .serializers import UserSerializer, GodzinyPracySerializer, WniosekUrlopowySerializer

import io
import xlsxwriter
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from .models import GodzinyPracy
from django.core.mail import send_mail

User = get_user_model()

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    # permission_classes = [IsAuthenticated, DjangoModelPermissions]
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        return Response(UserSerializer(request.user).data)

class GodzinyPracyViewSet(viewsets.ModelViewSet):
    queryset = GodzinyPracy.objects.all()
    serializer_class = GodzinyPracySerializer
    # permission_classes = [IsAuthenticated, DjangoModelPermissions]
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
    # permission_classes = [IsAuthenticated, DjangoModelPermissions]
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

        godziny = GodzinyPracy.objects.filter(user=user, rozpoczecie__year=rok, rozpoczecie__month=miesiac)
        urlopy = WniosekUrlopowy.objects.filter(user=user, data_od__year=rok, data_od__month=miesiac)

        return Response({
            "godziny_pracy": GodzinyPracySerializer(godziny, many=True).data,
            "urlopy": WniosekUrlopowySerializer(urlopy, many=True).data,
        })



def eksport_excel(request):
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    godziny = GodzinyPracy.objects.filter(user=request.user)
    worksheet.write(0, 0, "Data rozpoczęcia")
    worksheet.write(0, 1, "Data zakończenia")
    worksheet.write(0, 2, "Zatwierdzone")

    for idx, godzina in enumerate(godziny, start=1):
        worksheet.write(idx, 0, str(godzina.rozpoczecie))
        worksheet.write(idx, 1, str(godzina.zakonczenie))
        worksheet.write(idx, 2, "Tak" if godzina.zatwierdzone else "Nie")

    workbook.close()
    output.seek(0)
    response = HttpResponse(output, content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response['Content-Disposition'] = 'attachment; filename="godziny.xlsx"'
    return response


def eksport_pdf(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="godziny.pdf"'
    p = canvas.Canvas(response)

    godziny = GodzinyPracy.objects.filter(user=request.user)
    p.drawString(100, 800, "Godziny Pracy")

    y = 780
    for godzina in godziny:
        p.drawString(100, y,
                     f"{godzina.rozpoczecie} - {godzina.zakonczenie} ({'zatwierdzone' if godzina.zatwierdzone else 'oczekujące'})")
        y -= 20

    p.showPage()
    p.save()
    return response


def wyslij_powiadomienie_email(user, wiadomosc):
    send_mail(
        'Powiadomienie systemowe',
        wiadomosc,
        'admin@twojadomena.pl',
        [user.email],
        fail_silently=False,
    )