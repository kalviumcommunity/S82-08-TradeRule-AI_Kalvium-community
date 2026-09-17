import { NextResponse } from "next/server";

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const question = typeof body.question === "string" ? body.question.trim() : "";

    if (!question) {
      return NextResponse.json(
        { error: "A question is required." },
        { status: 400 }
      );
    }

    const backendBaseUrl =
      process.env.API_BASE_URL ||
      process.env.NEXT_PUBLIC_RAG_API_URL || "http://127.0.0.1:8000";

    const backendResponse = await fetch(`${backendBaseUrl}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (!backendResponse.ok) {
      const errorText = await backendResponse.text();
      return NextResponse.json(
        {
          error: "Backend chat endpoint returned an error.",
          detail: errorText,
        },
        { status: backendResponse.status }
      );
    }

    const payload = await backendResponse.json();

    return NextResponse.json({
      answer: payload.answer ?? "No answer was returned by the backend.",
      sources: payload.sources ?? [],
      status: payload.status ?? "answered",
      top_score: payload.top_score ?? null,
      retrieval_count: payload.retrieval_count ?? null,
      supporting_chunks: payload.supporting_chunks ?? null,
      reason: payload.reason ?? null,
      usage: payload.usage ?? null,
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: "Unable to reach the backend chat endpoint.",
        detail: error instanceof Error ? error.message : String(error),
      },
      { status: 500 }
    );
  }
}
