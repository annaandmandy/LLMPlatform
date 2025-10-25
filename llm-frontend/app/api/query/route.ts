import { NextRequest, NextResponse } from "next/server";

/**
 * API route to proxy query requests to the backend
 * This allows for server-side handling and additional processing if needed
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

    const response = await fetch(`${backendUrl}/query`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ error: "Unknown error" }));
      return NextResponse.json(
        { error: errorData.error || "Backend request failed" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("Error in query route:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
