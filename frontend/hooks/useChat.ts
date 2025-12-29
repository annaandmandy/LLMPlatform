import { useState, useCallback, useEffect } from 'react';
import Clarity from '@microsoft/clarity';
import type { LocationData } from './useLocation';
import { parseEventsToMessages } from '../lib/parseEvents';
import { getSession, streamQuery, logEvent } from '../lib/apiClient';

export interface Citation {
    title: string;
    url: string;
}

export interface ProductCardData {
    title: string;
    description?: string;
    price?: string;
    rating?: number;
    reviews_count?: number;
    image?: string;
    url: string;
    seller?: string;
    tag?: string;
    delivery?: string;
}

export interface Message {
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    citations?: Citation[];
    product_cards?: ProductCardData[];
    attachments?: { type: string; base64?: string; name?: string }[];
    options?: string[];
}

export interface AttachedMedia {
    name: string;
    type: 'image';
    previewUrl: string;
    dataUrl: string;
    mime: string;
    size: number;
}

interface UseChatOptions {
    userId: string;
    sessionId: string;
    location?: LocationData | null;
    isShoppingMode?: boolean;
}

const PRODUCT_KEYWORDS = /\b(buy|purchase|recommend|best|top|cheap|affordable|review|compare|product|price|shop|shopping|deal|sale|gift|where to get|looking for|need a|want a|headphones|laptop|phone|camera|shoes|watch|tv|tablet|speaker|earbuds|keyboard|mouse|monitor|chair|desk|mattress|vacuum|blender|coffee|toaster)\b/i;

function detectProductIntent(query: string): boolean {
    return PRODUCT_KEYWORDS.test(query);
}

export const AVAILABLE_MODELS = [
    { id: 'gpt-4o-mini-search-preview', name: 'GPT-4o mini', provider: 'openai' },
    { id: 'gpt-4o-search-preview', name: 'GPT-4o', provider: 'openai' },
    { id: 'gpt-5-search-api', name: 'GPT-5', provider: 'openai' },
    { id: 'x-ai/grok-3-mini:online', name: 'Grok 3 mini', provider: 'openrouter' },
    { id: 'perplexity/sonar:online', name: 'Perplexity Sonar', provider: 'openrouter' },
    { id: 'claude-sonnet-4-5-20250929', name: 'Claude 4.5 Sonnet', provider: 'anthropic' },
    { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', provider: 'google' },
];

export function useChat({ userId, sessionId, location, isShoppingMode = false }: UseChatOptions) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isReadOnly, setIsReadOnly] = useState(false);
    const [thinkingText, setThinkingText] = useState('');
    const [selectedModel, setSelectedModel] = useState('gpt-4o-mini-search-preview');
    const [memoryContext, setMemoryContext] = useState<Record<string, unknown> | null>(null);

    // Load messages from backend when session starts
    useEffect(() => {
        const loadSessionMessages = async () => {
            if (!sessionId) return;
            // Reset read-only state when changing sessions
            setIsReadOnly(false);

            try {
                const data = await getSession(sessionId, true);
                const loadedMessages = parseEventsToMessages(data.events || []);

                if (loadedMessages.length > 0) {
                    setMessages(loadedMessages);
                }

                // Check if session belongs to another user (Read Only Mode)
                if (data.user_id && userId && data.user_id !== userId) {
                    setIsReadOnly(true);
                }
            } catch (err) {
                // Session doesn't exist yet or other error
                if (err instanceof Error && err.message.includes('404')) {
                    return; // Session not found is OK
                }
                console.error('Failed to load session messages:', err);
            }
        };

        loadSessionMessages();
    }, [sessionId, userId]);

    const addMessage = useCallback((
        role: 'user' | 'assistant',
        content: string,
        citations?: Citation[],
        product_cards?: ProductCardData[],
        attachments?: { type: string; base64?: string; name?: string }[],
        options?: string[]
    ) => {
        setMessages((prev) => [
            ...prev,
            { role, content, citations, product_cards, attachments, options, timestamp: new Date() },
        ]);
    }, []);

    const sendMessage = useCallback(
        async (query: string, attachments: AttachedMedia[] = []) => {
            if (!query.trim() || !userId || !sessionId) {
                return;
            }

            const currentModel = AVAILABLE_MODELS.find((m) => m.id === selectedModel) || AVAILABLE_MODELS[0];
            const modelProvider = currentModel?.provider || 'openai';

            // Prepare payload
            const historyPayload = messages.slice(-6).map(({ role, content }) => ({ role, content }));
            const attachmentPayload = attachments.map((a) => ({
                type: a.type,
                name: a.name,
                mime: a.mime,
                base64: a.dataUrl,
                size: a.size,
            }));

            setIsLoading(true);

            // Set thinking text
            const isProductQuery = PRODUCT_KEYWORDS.test(query);
            const thinkingStatus = isProductQuery
                ? `Searching for products: ${query.slice(0, 80)}${query.length > 80 ? '...' : ''} `
                : query.slice(0, 100) + (query.length > 100 ? '...' : '');
            setThinkingText(thinkingStatus);

            // Add user message
            addMessage(
                'user',
                query,
                undefined,
                undefined,
                attachments.map((a) => ({ type: a.type, base64: a.dataUrl, name: a.name }))
            );

            // Set Clarity tags
            try {
                Clarity.setTag('selected_model', currentModel.id);
                Clarity.setTag('selected_model_name', currentModel.name);
                Clarity.setTag('selected_model_provider', modelProvider);
            } catch (err) {
                console.warn('Clarity tagging failed:', err);
            }

            try {
                // Use streaming endpoint via apiClient
                const stream = await streamQuery({
                    user_id: userId,
                    session_id: sessionId,
                    query,
                    model_name: currentModel.id,
                    model_provider: modelProvider,
                    web_search: true,
                    use_memory: true,
                    history: historyPayload,
                    location,
                    attachments: attachmentPayload,
                    mode: isShoppingMode ? 'shopping' : 'chat',
                });

                const reader = stream.getReader();
                const decoder = new TextDecoder();
                let buffer = '';
                let assistantMessage = '';
                let finalData: any = null;

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            const data = line.slice(6);
                            if (data === '[DONE]') {
                                break;
                            }

                            try {
                                const parsed = JSON.parse(data);

                                if (parsed.type === 'node') {
                                    // Update thinking text with node name
                                    setThinkingText(`Processing: ${parsed.node}...`);
                                } else if (parsed.type === 'final') {
                                    // Store final data
                                    finalData = parsed;
                                    assistantMessage = parsed.response || '';
                                } else if (parsed.type === 'error') {
                                    throw new Error(parsed.error);
                                }
                            } catch (e) {
                                if (data !== '[DONE]') {
                                    console.warn('Failed to parse SSE data:', data, e);
                                }
                            }
                        }
                    }
                }

                // Add final assistant message
                if (finalData) {
                    addMessage(
                        'assistant',
                        finalData.response,
                        finalData.citations,
                        finalData.product_cards,
                        finalData.attachments,
                        finalData.options
                    );
                    setMemoryContext(finalData.memory_context || null);
                }

                // Log browse event
                logEvent(sessionId, 'browse', {
                    query,
                    page_url: window.location.href,
                });
            } catch (err) {
                console.error('Error fetching query:', err);
                addMessage('assistant', `Failed to fetch response: ${err instanceof Error ? err.message : 'Unknown error'}`);
            } finally {
                setIsLoading(false);
                setThinkingText('');
            }
        },
        [userId, sessionId, location, isShoppingMode, selectedModel, messages, addMessage]
    );

    return {
        messages,
        isLoading,
        isReadOnly,
        thinkingText,
        selectedModel,
        setSelectedModel,
        memoryContext,
        sendMessage,
        setMessages,
    };
}
