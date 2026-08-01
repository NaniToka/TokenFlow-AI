import React, { useState } from 'react';
import { Play, Sparkles, Layers, Sliders, MessageSquare, Search, Filter } from 'lucide-react';
import { DEMO_PRESETS } from '../../data/demoConversation';
import Card from '../common/Card';

export default function DemoModeSelector({
  selectedPresetId,
  onSelectPreset,
  topK,
  onTopKChange,
  onRunCompression,
  isCompressing
}) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDomain, setSelectedDomain] = useState('All');

  const currentPreset = DEMO_PRESETS.find((p) => p.id === selectedPresetId) || DEMO_PRESETS[0];

  const domains = ['All', ...new Set(DEMO_PRESETS.map((p) => p.domain))];

  const filteredPresets = DEMO_PRESETS.filter((preset) => {
    const matchesDomain = selectedDomain === 'All' || preset.domain === selectedDomain;
    const matchesSearch =
      preset.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      preset.domain.toLowerCase().includes(searchQuery.toLowerCase()) ||
      preset.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesDomain && matchesSearch;
  });

  return (
    <Card
      title="Built-in Demo Conversation Scenarios"
      subtitle={`Explore 21+ industry-specific multi-turn scenarios (20–30 turns each)`}
      action={
        <div className="flex items-center gap-2">
          <span className="text-xs text-zinc-400 font-medium">Top-K Memory Turns:</span>
          <div className="flex items-center gap-2 bg-zinc-950 px-3 py-1 rounded-xl border border-white/5">
            <input
              type="range"
              min="1"
              max="10"
              value={topK}
              onChange={(e) => onTopKChange(Number(e.target.value))}
              className="w-24 accent-emerald-500 cursor-pointer"
            />
            <span className="text-xs font-bold text-emerald-400 w-4 text-center">{topK}</span>
          </div>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Search & Domain Filter Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-zinc-950/60 p-3 rounded-xl border border-zinc-800">
          <div className="relative w-full sm:w-72">
            <Search className="w-4 h-4 text-zinc-400 absolute left-3 top-2.5" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search scenarios by industry or topic..."
              className="glass-input pl-9 pr-4 py-1.5 text-xs w-full"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto overflow-x-auto pb-1 sm:pb-0">
            <Filter className="w-3.5 h-3.5 text-zinc-400 shrink-0" />
            <select
              value={selectedDomain}
              onChange={(e) => setSelectedDomain(e.target.value)}
              className="glass-input text-xs px-3 py-1.5 bg-zinc-900 border-zinc-800 text-zinc-200"
            >
              {domains.map((domain) => (
                <option key={domain} value={domain}>
                  {domain}
                </option>
              ))}
            </select>
            <span className="text-[11px] text-zinc-500 font-mono shrink-0">
              ({filteredPresets.length} scenarios)
            </span>
          </div>
        </div>

        {/* Preset Selector Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 max-h-[540px] overflow-y-auto pr-1">
          {filteredPresets.map((preset) => {
            const isSelected = preset.id === currentPreset.id;
            return (
              <div
                key={preset.id}
                onClick={() => onSelectPreset(preset.id)}
                className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 flex flex-col justify-between ${
                  isSelected
                    ? 'bg-emerald-500/10 border-emerald-500/50 shadow-lg shadow-emerald-500/10'
                    : 'bg-zinc-950/60 border-zinc-800 hover:border-zinc-700'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                      {preset.domain}
                    </span>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400">
                      {preset.history.length} turns
                    </span>
                  </div>

                  <h4 className={`text-xs font-bold mb-1 ${isSelected ? 'text-emerald-400' : 'text-zinc-200'}`}>
                    {preset.title}
                  </h4>
                  <p className="text-[11px] text-zinc-400 leading-relaxed mb-3 line-clamp-2">
                    {preset.description}
                  </p>
                </div>

                <div className="flex items-center justify-between text-[10px] text-zinc-500 font-mono border-t border-white/5 pt-2 mt-auto">
                  <span className="truncate max-w-[170px]">Q: {preset.current_message}</span>
                  <span className={isSelected ? 'text-emerald-400 font-semibold' : 'text-zinc-500'}>
                    {isSelected ? '✓ Selected' : 'Load'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Selected Preset Action Footer */}
        <div className="p-4 rounded-xl bg-zinc-950/80 border border-zinc-800 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shrink-0">
              <MessageSquare className="w-5 h-5" />
            </div>
            <div>
              <p className="text-xs font-bold text-zinc-200 flex items-center gap-2">
                <span>{currentPreset.title}</span>
                <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">
                  {currentPreset.domain}
                </span>
              </p>
              <p className="text-[11px] text-zinc-400">
                Ready to compress <strong className="text-zinc-200">{currentPreset.history.length} history turns</strong> with query: "{currentPreset.current_message.slice(0, 50)}..."
              </p>
            </div>
          </div>

          <button
            onClick={onRunCompression}
            disabled={isCompressing}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 hover:from-emerald-400 hover:to-cyan-400 text-zinc-950 font-bold text-xs shadow-lg shadow-emerald-500/20 transition-all active:scale-95 disabled:opacity-50 shrink-0"
          >
            <Sparkles className={`w-4 h-4 ${isCompressing ? 'animate-spin' : ''}`} />
            <span>{isCompressing ? 'Compressing Memory...' : 'Run TokenFlow Compression'}</span>
          </button>
        </div>
      </div>
    </Card>
  );
}
