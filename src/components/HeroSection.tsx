import React, { useState, useRef, useEffect, ChangeEvent, KeyboardEvent } from "react";
import { useQuery } from '@tanstack/react-query';
import { crewApi } from "../lib/api";

export const HeroSection: React.FC = () => {
  const [input, setInput] = useState<string>("");
  const [topic, setTopic] = useState<string>("");
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);
  const [crewResult, setCrewResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const {data, isPending, error} = useQuery({
    queryKey: ['agentSearch', topic],
    queryFn: () => crewApi.kickoffCrew(topic),
    enabled: !!topic.trim(), //&& !isLoading,
  });

  // Auto-resize the text input field up to a comfortable max height
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  }, [input]);

  const handleInputChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  const handleSend = () => {
    // if (!topic.trim() || isLoading) return;
    setIsLoading(true);
    
    setTopic(input.trim());
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const suggestions = [
    "✨ Medieval European History",
    "🚀 Machine Learning Fundamentals",
    "🧠 Stoicism and Modern Life"
  ];

  return (
    <section className="relative min-h-[85vh] w-full flex flex-col items-center justify-center bg-[#09090b] text-white px-4 py-20 overflow-hidden">
      
      {/* --- BACKGROUND GLOWS (Simple & Clean) --- */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-indigo-600/10 rounded-full blur-[120px] pointer-events-none" />
      <div className="absolute top-1/2 left-1/3 w-[300px] h-[300px] bg-sky-500/5 rounded-full blur-[100px] pointer-events-none" />

      {/* --- HERO CONTENT --- */}
      <div className="relative z-10 w-full max-w-3xl text-center flex flex-col items-center">
        
        {/* Subtle Announcement Tag */}
        <div className="inline-flex items-center gap-2 px-3 py-1 text-xs font-medium bg-zinc-900 border border-zinc-800 rounded-full text-zinc-400 mb-6 tracking-wide">
          <span className="h-1.5 w-1.5 rounded-full bg-indigo-400" />
          Now in Beta
        </div>

        {/* Clean, Bold Headline */}
        <h1 className="text-4xl sm:text-6xl font-bold tracking-tight mb-6 bg-clip-text text-transparent bg-gradient-to-b from-white to-zinc-400 leading-[1.15]">
          Turn any topic <br />
          <span className="bg-clip-text text-transparent bg-gradient-to-r from-indigo-400 via-purple-400 to-pink-400">
            into a real reading journey.
          </span>
        </h1>

        {/* Short, Conversational Subtitle */}
        <p className="text-zinc-400 text-base sm:text-lg max-w-xl mb-10 leading-relaxed font-normal">
          Enter a topic. Get a structured course with real books, thoughtful assignments, and no AI summaries — just deep reading and thinking.
        </p>

        {/* --- PROMPT INPUT BOX --- */}
        <div className="w-full relative group max-w-2xl">
          {/* Subtle responsive backglow when user is focused on typing */}
          <div className="absolute -inset-px bg-gradient-to-r from-indigo-500 to-purple-500 rounded-2xl opacity-30 group-focus-within:opacity-70 blur-sm transition duration-300" />
          
          {/* Main Container */}
          <div className="relative flex items-end gap-2 p-3 bg-zinc-950/80 border border-zinc-800 rounded-2xl shadow-2xl backdrop-blur-md">
            
            {/* Context/Attachment Shortcut */}
            <button 
              className="flex items-center justify-center p-2 rounded-xl text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900/50 transition duration-150"
              aria-label="Add context asset"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
              </svg>
            </button>

            {/* Smart Expanding Textarea */}
            <textarea
              ref={textareaRef}
              rows={1}
              value={input}
              onChange={handleInputChange}
              onKeyDown={handleKeyDown}
              placeholder="Enter a topic you want to master..."
              disabled={isLoading}
              className="flex-1 max-h-48 min-h-[24px] py-1.5 resize-none bg-transparent text-zinc-100 placeholder-zinc-500 focus:outline-none text-[15px] leading-relaxed disabled:opacity-50"
            />

            {/* Submit / Action Button */}
            <button
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
              className={`flex items-center justify-center p-2.5 rounded-xl transition-all duration-200 
                ${!input.trim() || isLoading
                  ? "bg-zinc-900 text-zinc-600 cursor-not-allowed" 
                  : "bg-white hover:bg-zinc-200 text-black shadow-md shadow-white/10 active:scale-95"
                }`}
              aria-label="Send query"
            >
              {isLoading ? (
                /* Spinner state */
                <svg className="animate-spin h-4 w-4 text-black" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              ) : (
                /* Clear Right Chevron Arrow icon */
                <svg className="h-4 w-4 stroke-current" viewBox="0 0 24 24" fill="none" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="9 18 15 12 9 6" />
                </svg>
              )}
            </button>
          </div>
        </div>

        {/* --- RELEVANT CLICKABLE SUGGESTIONS --- */}
        <div className="flex flex-wrap items-center justify-center gap-2 mt-5">
          <span className="text-xs text-zinc-500 mr-1">Try:</span>
          {suggestions.map((suggestion, index) => (
            <button
              key={index}
              onClick={() => setInput(suggestion.replace(/^[^\s]+\s/, ""))}
              className="px-3 py-1 rounded-lg text-xs text-zinc-400 bg-zinc-900/40 hover:bg-zinc-900 border border-zinc-800/80 hover:border-zinc-700 hover:text-zinc-200 transition-all duration-150 active:scale-95"
            >
              {suggestion}
            </button>
          ))}
        </div>

      </div>
    </section>
  );
};