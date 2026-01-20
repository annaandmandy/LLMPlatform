
import React, { useState, useEffect } from 'react';

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
    const [isOpen, setIsOpen] = useState(false); // Default to collapsed

    if (!thoughts || thoughts.length === 0) return null;

    return (
        <div className="my-2">
            {/* Minimal Trigger */}
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 text-xs text-slate-400 hover:text-slate-600 transition-colors select-none"
            >
                <span className={`transform transition-transform duration-200 ${isOpen ? 'rotate-90' : ''}`}>
                    ▶
                </span>
                <span className="font-medium">
                    {isComplete ? 'Processed' : 'Thinking'}
                </span>

                {!isComplete && (
                    <span className="flex gap-1 ml-1">
                        <span className="w-1 h-1 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0s' }}></span>
                        <span className="w-1 h-1 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></span>
                        <span className="w-1 h-1 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                    </span>
                )}
            </button>

            {/* Expanded Content */}
            {isOpen && (
                <div className="mt-2 pl-2 border-l-2 border-slate-100 ml-1 space-y-3 py-1">
                    {thoughts.map((thought, idx) => (
                        <div key={idx} className="pl-3 text-xs">
                            <div className="flex items-center gap-2 text-slate-700 font-medium">
                                <span>{thought.agent}</span>
                                <span className="text-[10px] text-slate-400 font-normal opacity-75">
                                    {new Date(thought.timestamp).toLocaleTimeString([], { minute: '2-digit', second: '2-digit' })}
                                </span>
                            </div>
                            <div className="text-slate-500 mt-0.5">
                                {thought.status}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
