import React, { useState } from 'react';

export interface Thought {
    agent: string;
    status: string;
    timestamp: number;
}

interface ThinkingProcessProps {
    thoughts: Thought[];
    isComplete?: boolean;
}

export default function ThinkingProcess({ thoughts, isComplete = false }: ThinkingProcessProps) {
    const [isOpen, setIsOpen] = useState(true);

    if (!thoughts || thoughts.length === 0) return null;

    return (
        <div className="mb-4 rounded-lg border border-slate-200 bg-slate-50 overflow-hidden">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="w-full px-4 py-2 flex items-center justify-between text-xs font-medium text-slate-600 bg-slate-100 hover:bg-slate-200 transition-colors"
                title="Toggle thinking process"
            >
                <div className="flex items-center gap-2">
                    {isComplete ? (
                        <span className="text-green-600">✓ Finished Thinking</span>
                    ) : (
                        <span className="flex items-center gap-2 text-blue-600">
                            <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
                            Thinking Process...
                        </span>
                    )}
                    <span className="bg-slate-200 px-1.5 py-0.5 rounded-full text-[10px] text-slate-500">
                        {thoughts.length} steps
                    </span>
                </div>
                <span className={`transform transition-transform ${isOpen ? 'rotate-180' : ''}`}>
                    ▼
                </span>
            </button>

            {isOpen && (
                <div className="p-3 text-xs space-y-2 bg-slate-50 border-t border-slate-200">
                    {thoughts.map((thought, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-slate-700">
                            <div className="w-5 flex justify-center shrink-0">
                                {idx === thoughts.length - 1 && !isComplete ? (
                                    <span className="animate-spin">⚙️</span>
                                ) : (
                                    <span>🤖</span>
                                )}
                            </div>
                            <div className="flex-1">
                                <span className="font-semibold text-slate-800">{thought.agent}</span>
                                <span className="mx-1 text-slate-400">→</span>
                                <span className="text-slate-600">{thought.status}</span>
                            </div>
                            <span className="text-[10px] text-slate-400 font-mono">
                                {new Date(thought.timestamp).toLocaleTimeString([], { minute: '2-digit', second: '2-digit' })}
                            </span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
