import { Navigate, createBrowserRouter } from 'react-router-dom';
import { AuthGuard, GuestGuard, RoleGuard } from '@/app/guards';
import { AdminLayout, CandidateLayout, EmployerLayout } from '@/app/layouts';
import { LandingPage } from '@/pages/LandingPage';
import { LoginPage } from '@/pages/auth/LoginPage';
import { RegisterPage } from '@/pages/auth/RegisterPage';
import { CandidateDashboardPage } from '@/pages/candidate/DashboardPage';
import { CandidateProfilePage } from '@/pages/candidate/ProfilePage';
import { CandidateProfileEditPage } from '@/pages/candidate/ProfileEditPage';
import { CandidateFspPage } from '@/pages/candidate/FspPage';
import { CandidateOffersPage } from '@/pages/candidate/OffersPage';
import { CandidateOfferDetailPage } from '@/pages/candidate/OfferDetailPage';
import { CandidateTestingPage } from '@/pages/candidate/TestingPage';
import { CandidateTestingSessionPage } from '@/pages/candidate/TestingSessionPage';
import { CandidateTestingResultPage } from '@/pages/candidate/TestingResultPage';
import { CandidateVacanciesPage } from '@/pages/candidate/VacanciesPage';
import { CandidateVacancyDetailPage } from '@/pages/candidate/VacancyDetailPage';
import { EmployerDashboardPage } from '@/pages/employer/DashboardPage';
import { EmployerTalentPoolPage } from '@/pages/employer/TalentPoolPage';
import { EmployerCandidateDetailPage } from '@/pages/employer/CandidateDetailPage';
import { EmployerVacanciesPage } from '@/pages/employer/VacanciesPage';
import { EmployerVacancyFormPage } from '@/pages/employer/VacancyFormPage';
import { EmployerVacancyDetailPage } from '@/pages/employer/VacancyDetailPage';
import { EmployerOffersPage } from '@/pages/employer/OffersPage';
import { EmployerShortlistPage } from '@/pages/employer/ShortlistPage';
import { EmployerComparePage } from '@/pages/employer/ComparePage';
import { CareerPassportPage } from '@/pages/public/CareerPassportPage';
import { LegalPage } from '@/pages/public/LegalPage';
import { UiKitPage } from '@/pages/public/UiKitPage';
import { NotificationsPage } from '@/pages/shared/NotificationsPage';
import { AdminOverviewPage } from '@/pages/admin/OverviewPage';
import { AdminUsersPage } from '@/pages/admin/UsersPage';
import { AdminOffersPage } from '@/pages/admin/OffersPage';
import { AdminVacanciesPage } from '@/pages/admin/VacanciesPage';
import { AdminAssessmentsPage } from '@/pages/admin/AssessmentsPage';
import { AdminCategoriesPage } from '@/pages/admin/CategoriesPage';

export const router = createBrowserRouter([
  { path: '/', element: <LandingPage /> },
  { path: '/ui-kit', element: <UiKitPage /> },
  { path: '/terms', element: <LegalPage slug="terms" /> },
  { path: '/privacy', element: <LegalPage slug="privacy" /> },
  { path: '/p/:slug', element: <CareerPassportPage /> },
  {
    element: <GuestGuard />,
    children: [
      { path: '/login', element: <LoginPage /> },
      { path: '/register', element: <RegisterPage /> },
    ],
  },
  {
    element: <AuthGuard />,
    children: [
      {
        element: <RoleGuard allow={['candidate']} />,
        children: [
          {
            path: '/candidate',
            element: <CandidateLayout />,
            children: [
              { index: true, element: <CandidateDashboardPage /> },
              { path: 'profile', element: <CandidateProfilePage /> },
              { path: 'profile/edit', element: <CandidateProfileEditPage /> },
              { path: 'fsp', element: <CandidateFspPage /> },
              { path: 'offers', element: <CandidateOffersPage /> },
              { path: 'offers/:id', element: <CandidateOfferDetailPage /> },
              { path: 'testing', element: <CandidateTestingPage /> },
              { path: 'testing/result', element: <CandidateTestingResultPage /> },
              { path: 'testing/:sessionId', element: <CandidateTestingSessionPage /> },
              { path: 'vacancies', element: <CandidateVacanciesPage /> },
              { path: 'vacancies/:id', element: <CandidateVacancyDetailPage /> },
              { path: 'notifications', element: <NotificationsPage /> },
            ],
          },
        ],
      },
      {
        element: <RoleGuard allow={['employer']} />,
        children: [
          {
            path: '/employer',
            element: <EmployerLayout />,
            children: [
              { index: true, element: <EmployerDashboardPage /> },
              { path: 'talent-pool', element: <EmployerTalentPoolPage /> },
              { path: 'candidates/:id', element: <EmployerCandidateDetailPage /> },
              { path: 'vacancies', element: <EmployerVacanciesPage /> },
              { path: 'vacancies/new', element: <EmployerVacancyFormPage mode="create" /> },
              { path: 'vacancies/:id', element: <EmployerVacancyDetailPage /> },
              { path: 'vacancies/:id/edit', element: <EmployerVacancyFormPage mode="edit" /> },
              { path: 'offers', element: <EmployerOffersPage /> },
              { path: 'shortlist', element: <EmployerShortlistPage /> },
              { path: 'compare', element: <EmployerComparePage /> },
              { path: 'notifications', element: <NotificationsPage /> },
            ],
          },
        ],
      },
      {
        element: <RoleGuard allow={['admin']} />,
        children: [
          {
            path: '/admin',
            element: <AdminLayout />,
            children: [
              { index: true, element: <Navigate to="/admin/overview" replace /> },
              { path: 'overview', element: <AdminOverviewPage /> },
              { path: 'users', element: <AdminUsersPage /> },
              { path: 'assessments', element: <AdminAssessmentsPage /> },
              { path: 'categories', element: <AdminCategoriesPage /> },
              { path: 'offers', element: <AdminOffersPage /> },
              { path: 'vacancies', element: <AdminVacanciesPage /> },
            ],
          },
        ],
      },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
]);

