from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import UserViewSet, GodzinyPracyViewSet, WniosekUrlopowyViewSet, eksport_excel, eksport_pdf, GrafikViewSet, \
    user_profile_api
from dj_rest_auth.views import LoginView, LogoutView
from dj_rest_auth.registration.views import RegisterView
from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
from dj_rest_auth.registration.views import SocialLoginView

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'godziny', GodzinyPracyViewSet)
router.register(r'wnioski', WniosekUrlopowyViewSet)
router.register(r'grafik', GrafikViewSet, basename='grafik')


class GoogleLogin(SocialLoginView):
    adapter_class = GoogleOAuth2Adapter


urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('', include(router.urls)),
]

urlpatterns += [
    path('auth/login/', LoginView.as_view(), name='rest_login'),
    path('auth/logout/', LogoutView.as_view(), name='rest_logout'),
    path('auth/register/', RegisterView.as_view(), name='rest_register'),
    path('auth/google/', GoogleLogin.as_view(), name='google_login'),
]

urlpatterns += [
    path('eksport/excel/', eksport_excel, name="eksport_excel"),
    path('eksport/pdf/', eksport_pdf, name="eksport_pdf"),
]

urlpatterns += [
    path('profile/', user_profile_api, name='user_profile'),
]
