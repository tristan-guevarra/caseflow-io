'use client';

import { useState } from 'react';
import { useSearch } from '@/hooks/useApi';
import Link from 'next/link';
import { Search, Sparkles, FileText, ArrowRight } from 'lucide-react';

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const search = useSearch();

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim()) search.mutate({ query: query.trim() });
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="page-header text-center">
        <div className="inline-flex items-center gap-2 badge-indigo mb-3 text-sm">
          <Sparkles className="h-3.5 w-3.5" /> Powered by AI
        </div>
        <h1 className="text-3xl font-bold text-slate-900">Search Across All Documents</h1>
        <p className="page-description mt-2">Ask questions in plain English. We&apos;ll search every document in your matters using semantic understanding.</p>
      </div>

      {/* search bar */}
      <form onSubmit={handleSearch} className="relative mb-8">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
        <input
          className="w-full rounded-2xl border border-slate-300 bg-white pl-12 pr-32 py-4 text-base text-slate-900 shadow-sm placeholder:text-slate-400 focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 transition-all"
          placeholder='e.g., "What are the indemnification terms in the Meridian deal?"'
          value={query}
          onChange={e => setQuery(e.target.value)}
        />
        <button type="submit" disabled={search.isPending || !query.trim()} className="btn-primary absolute right-2 top-1/2 -translate-y-1/2">
          {search.isPending ? 'Searching...' : 'Search'}
        </button>
      </form>

      {/* search results */}
      {search.data && (
        <div className="animate-fade-in">
          <p className="text-sm text-slate-500 mb-4">{search.data.total} results for &ldquo;{search.data.query}&rdquo;</p>
          <div className="space-y-4">
            {search.data.results.map((result, i) => (
              <Link key={i} href={`/matters/${result.matter_id}`} className="card p-5 block hover:shadow-md transition-shadow group">
                <div className="flex items-center gap-3 mb-2">
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-50">
                    <FileText className="h-4 w-4 text-red-500" />
                  </div>
                  <div>
                    <p className="text-sm font-bold text-slate-900 group-hover:text-indigo-600 transition-colors">{result.document_filename}</p>
                    <p className="text-xs text-slate-400">{result.matter_title}</p>
                  </div>
                  <div className="ml-auto flex items-center gap-2">
                    <span className="badge-green text-[10px]">{Math.round(result.similarity_score * 100)}% match</span>
                    <ArrowRight className="h-4 w-4 text-slate-300 group-hover:text-indigo-500 transition-colors" />
                  </div>
                </div>
                <p className="text-sm text-slate-600 leading-relaxed line-clamp-3 pl-11">{result.chunk_text}</p>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* no results state */}
      {search.data && search.data.results.length === 0 && (
        <div className="text-center py-12">
          <Search className="h-10 w-10 text-slate-300 mx-auto mb-3" />
          <p className="text-sm text-slate-500">No matching documents found. Try a different query.</p>
        </div>
      )}

      {/* suggested queries */}
      {!search.data && !search.isPending && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-4">
          {[
            'What deadlines are coming up this month?',
            'Show me all risk flags across my matters',
            'What are the key terms in the purchase agreement?',
            'Find documents related to patent infringement',
          ].map(suggestion => (
            <button
              key={suggestion}
              onClick={() => { setQuery(suggestion); search.mutate({ query: suggestion }); }}
              className="text-left rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-600 hover:border-indigo-300 hover:bg-indigo-50 transition-all"
            >
              <Search className="h-3.5 w-3.5 inline mr-2 text-slate-400" />{suggestion}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
