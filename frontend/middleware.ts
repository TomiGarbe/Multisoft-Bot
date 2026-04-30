import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

const publicRoutes = ['/', '/login'];
const protectedRoutes = ['/dashboard', '/users', '/roles', '/negocios', '/advisors', '/conversaciones', '/canales', '/configuracion'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const accessToken = request.cookies.get('access_token')?.value;
  const isPublicRoute = publicRoutes.includes(pathname);
  const isProtectedRoute = protectedRoutes.some(
    (route) => pathname === route || pathname.startsWith(`${route}/`)
  );

  if (pathname === '/') {
    return NextResponse.redirect(new URL(accessToken ? '/dashboard' : '/login', request.url));
  }

  if (isPublicRoute && accessToken && pathname === '/login') {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  if (isProtectedRoute && !accessToken) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
};

