import { NextRequest, NextResponse } from "next/server";

// This is a simple API route for demo purposes
// In production, this would interact with your backend database

export async function GET(request: NextRequest) {
  // For now, this is handled client-side via localStorage
  // But this endpoint can be extended to fetch from backend
  return NextResponse.json({ message: "Sessions are stored in localStorage for demo" });
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { userId, sessionId, title, lastMessage } = body;

    // In production, save to database here
    // For now, return success as client handles localStorage

    return NextResponse.json({
      success: true,
      session: {
        id: sessionId,
        title,
        lastMessage,
        timestamp: new Date().toISOString(),
      },
    });
  } catch (error) {
    console.error("Error saving session:", error);
    return NextResponse.json(
      { error: "Failed to save session" },
      { status: 500 }
    );
  }
}
