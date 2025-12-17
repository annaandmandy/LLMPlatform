"use client";

import { use } from 'react';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

/**
 * Dynamic route for individual chat sessions
 * URL: /chat/{sessionId}
 * 
 * This allows users to:
 * - Share chat sessions via URL
 * - Bookmark specific conversations
 * - Navigate directly to a session
 */
export default function ChatPage({ params }: { params: Promise<{ sessionId: string }> }) {
    const { sessionId } = use(params);
    const router = useRouter();

    useEffect(() => {
        // Redirect to home with session ID as query param
        // The main page will handle loading the session
        router.push(`/?session=${sessionId}`);
    }, [sessionId, router]);

    return (
        <div className="h-screen flex items-center justify-center">
            <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading chat session...</p>
            </div>
        </div>
    );
}
