import { NextResponse } from "next/server";

export async function GET() {
  try {
    const backendBaseUrl =
      process.env.API_BASE_URL ||
      process.env.NEXT_PUBLIC_API_BASE_URL ||
      "http://localhost:8000";

    const response = await fetch(`${backendBaseUrl}/health`, {
      method: "GET",
      cache: "no-store",
    });

    if (!response.ok) {
      return NextResponse.json(
        {
          frontend: "ok",
          backend: "unavailable",
          status: response.status,
        },
        { status: 200 }
      );
    }

    const payload = await response.json();

    return NextResponse.json({
      frontend: "ok",
      backend: payload,
    });
  } catch {
    return NextResponse.json(
      {
        frontend: "ok",
        backend: "unavailable",
      },
      { status: 200 }
    );
  }
}
