import React, { useState, useEffect } from 'react';
import { MessageCircle, Music, Play, Terminal, Shield, Activity, CheckCircle2 } from 'lucide-react';

const Facebook = (props: React.ComponentPropsWithoutRef<'svg'>) => (
  <svg
    viewBox="0 0 24 24"
    width="24"
    height="24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M18 2h-3a5 5 0 0 0-5 5v3H7v4h3v8h4v-8h3l1-4h-4V7a1 1 0 0 1 1-1h3z" />
  </svg>
);

const Instagram = (props: React.ComponentPropsWithoutRef<'svg'>) => (
  <svg
    viewBox="0 0 24 24"
    width="24"
    height="24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <rect x="2" y="2" width="20" height="20" rx="5" ry="5" />
    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z" />
    <line x1="17.5" y1="6.5" x2="17.51" y2="6.5" />
  </svg>
);

const Twitter = (props: React.ComponentPropsWithoutRef<'svg'>) => (
  <svg
    viewBox="0 0 24 24"
    width="24"
    height="24"
    fill="none"
    stroke="currentColor"
    strokeWidth="2"
    strokeLinecap="round"
    strokeLinejoin="round"
    {...props}
  >
    <path d="M23 3a10.9 10.9 0 0 1-3.14 1.53 4.48 4.48 0 0 0-7.86 3v1A10.66 10.66 0 0 1 3 4s-4 9 5 13a11.64 11.64 0 0 1-7 2c9 5 20 0 20-11.5a4.5 4.5 0 0 0-.08-.83A7.72 7.72 0 0 0 23 3z" />
  </svg>
);


export default function App() {
  const [platform, setPlatform] = useState('Facebook');
  const [target, setTarget] = useState('');
  const [count, setCount] = useState(1);
  const [isRunning, setIsRunning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState<{ message: string; level: string; timestamp: string }[]>([]);
  const [status, setStatus] = useState<string>('idle');
  const [promptText, setPromptText] = useState<string | null>(null);
  const [animatedProgress, setAnimatedProgress] = useState(0);
  const [isPulsing, setIsPulsing] = useState(false);
  const [logsCountAtLastMilestone, setLogsCountAtLastMilestone] = useState(0);

  const logsEndRef = React.useRef<HTMLDivElement>(null);

  // Sync milestone log count
  useEffect(() => {
    setLogsCountAtLastMilestone(logs.length);
  }, [progress]);

  const segmentSize = 100 / count;
  const currentStepLogsCount = Math.max(0, logs.length - logsCountAtLastMilestone);
  const estimatedLogsPerCycle = 8;
  const segmentProgress = Math.min(0.95, currentStepLogsCount / estimatedLogsPerCycle);
  const targetProgress = isRunning
    ? Math.min(99.5, progress + (segmentProgress * segmentSize))
    : progress;

  // Smoothly interpolate progress animation
  useEffect(() => {
    if (!isRunning) {
      if (progress === 0) {
        setAnimatedProgress(0);
      } else {
        let animationId: number;
        const animate = () => {
          setAnimatedProgress((prev) => {
            const diff = progress - prev;
            if (Math.abs(diff) < 0.1) {
              return progress;
            }
            animationId = requestAnimationFrame(animate);
            return prev + diff * 0.15;
          });
        };
        animate();
        return () => cancelAnimationFrame(animationId);
      }
      return;
    }

    let animationId: number;
    const animate = () => {
      setAnimatedProgress((prev) => {
        const diff = targetProgress - prev;
        if (Math.abs(diff) < 0.1) {
          return targetProgress;
        }
        animationId = requestAnimationFrame(animate);
        return prev + diff * 0.08;
      });
    };

    animate();
    return () => cancelAnimationFrame(animationId);
  }, [targetProgress, isRunning, progress]);

  // Pulse the launch button on new logs
  useEffect(() => {
    if (logs.length > 0 && isRunning) {
      setIsPulsing(true);
      const timer = setTimeout(() => setIsPulsing(false), 250);
      return () => clearTimeout(timer);
    }
  }, [logs.length, isRunning]);

  const platforms = [
    { name: 'Facebook', icon: <Facebook className="w-5 h-5" />, color: 'text-blue-500', bg: 'bg-blue-500/10', border: 'border-blue-500', glow: 'shadow-blue-500/20' },
    { name: 'Instagram', icon: <Instagram className="w-5 h-5" />, color: 'text-pink-500', bg: 'bg-pink-500/10', border: 'border-pink-500', glow: 'shadow-pink-500/20' },
    { name: 'Threads', icon: <MessageCircle className="w-5 h-5" />, color: 'text-gray-100', bg: 'bg-gray-100/10', border: 'border-gray-100', glow: 'shadow-gray-100/20' },
    { name: 'TikTok', icon: <Music className="w-5 h-5" />, color: 'text-red-500', bg: 'bg-red-500/10', border: 'border-red-500', glow: 'shadow-red-500/20' },
    { name: 'Twitter', icon: <Twitter className="w-5 h-5" />, color: 'text-sky-400', bg: 'bg-sky-400/10', border: 'border-sky-400', glow: 'shadow-sky-400/20' },
  ];

  // Synchronize with backend status and events on mount
  useEffect(() => {
    const es = new EventSource('http://localhost:5000/api/events');

    es.onmessage = (event) => {
      try {
        const parsed = JSON.parse(event.data);
        if (parsed.type === 'log') {
          setLogs((prev) => [...prev, parsed.data]);
        } else if (parsed.type === 'progress') {
          setProgress(parsed.data.percent);
        } else if (parsed.type === 'status') {
          setIsRunning(parsed.data.isRunning);
          setStatus(parsed.data.status);
        } else if (parsed.type === 'prompt') {
          setPromptText(parsed.data.text);
        }
      } catch (e) {
        console.error('Failed to parse event', e);
      }
    };

    es.onerror = (e) => {
      console.error('SSE connection error:', e);
    };

    return () => {
      es.close();
    };
  }, []);

  // Auto-scroll logs
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  // Automatically reset UI and clear logs 4 seconds after sequence ends
  useEffect(() => {
    if (status === 'completed' || status === 'stopped' || status === 'error') {
      const timer = setTimeout(() => {
        setLogs([]);
        setProgress(0);
        setAnimatedProgress(0);
        setStatus('idle');
      }, 4000);
      return () => clearTimeout(timer);
    }
  }, [status]);



  const handleStart = async () => {
    if (!target) return;
    setIsRunning(true);
    setProgress(0);
    setLogsCountAtLastMilestone(0);
    setPromptText(null);
    setLogs([]);
    setStatus('running');

    try {
      const response = await fetch('http://localhost:5000/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          platform: platform.toLowerCase(),
          url: target,
          count: count,
        }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.error || 'Failed to start automation');
      }
    } catch (err: any) {
      setLogs((prev) => [
        ...prev,
        {
          message: err.message || 'Error communicating with backend server.',
          level: 'ERROR',
          timestamp: new Date().toLocaleTimeString(),
        },
      ]);
      setIsRunning(false);
      setStatus('error');
    }
  };

  const handleStop = async () => {
    try {
      await fetch('http://localhost:5000/api/stop', { method: 'POST' });
    } catch (e) {
      console.error('Failed to stop automation', e);
    }
  };

  const handleConfirmLogin = async () => {
    try {
      await fetch('http://localhost:5000/api/confirm-login', { method: 'POST' });
      setPromptText(null);
    } catch (e) {
      console.error('Failed to confirm login', e);
    }
  };

  const isValidUrl = (url: string, selectedPlatform: string): boolean => {
    if (!url) return false;
    const lowerUrl = url.toLowerCase();

    switch (selectedPlatform.toLowerCase()) {
      case 'facebook':
        return lowerUrl.includes('facebook.com') || lowerUrl.includes('fb.com');
      case 'instagram':
        return lowerUrl.includes('instagram.com');
      case 'threads':
        return lowerUrl.includes('threads.net') || lowerUrl.includes('threads.com');
      case 'tiktok':
        return lowerUrl.includes('tiktok.com');
      case 'twitter':
        return lowerUrl.includes('twitter.com') || lowerUrl.includes('x.com');
      default:
        return true;
    }
  };

  const isUrlValid = !target || isValidUrl(target, platform);

  const selectedData = platforms.find(p => p.name === platform) || platforms[0];

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-neutral-200 flex font-sans selection:bg-blue-500/30 relative overflow-hidden">

      <div className="absolute top-0 left-1/2 w-[800px] h-[800px] bg-blue-600/5 rounded-full blur-[120px] -translate-x-1/2 -translate-y-1/2 pointer-events-none"></div>

      <div className="w-72 border-r border-white/5 bg-black/40 backdrop-blur-xl p-6 flex flex-col z-10">
        <div className="mb-10 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Shield className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold tracking-wide text-white">SMAR</h1>
            <p className="text-xs text-neutral-500 uppercase tracking-widest font-medium">Automation Suite</p>
          </div>
        </div>

        <div className="text-xs font-semibold text-neutral-500 mb-4 uppercase tracking-wider">Select Platform</div>

        <nav className="flex-1 space-y-2">
          {platforms.map((p) => (
            <button
              key={p.name}
              onClick={() => {
                setPlatform(p.name);
                setProgress(0);
                setIsRunning(false);
                if (target && !isValidUrl(target, p.name)) {
                  setTarget('');
                }
              }}
              className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-xl transition-all duration-300 ${platform === p.name
                  ? `${p.bg} ${p.color} font-medium shadow-lg ${p.glow} border border-white/5`
                  : 'text-neutral-400 hover:bg-white/5 hover:text-neutral-200 border border-transparent'
                }`}
            >
              {p.icon}
              {p.name}
              {platform === p.name && (
                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-current animate-pulse"></div>
              )}
            </button>
          ))}
        </nav>

        <div className="pt-6 border-t border-white/5 mt-auto">
          <div className="flex items-start gap-3 text-neutral-500 text-xs bg-blue-950/10 px-4 py-3 rounded-xl border border-blue-500/20 shadow-[0_0_15px_rgba(59,130,246,0.07)] hover:border-blue-500/40 hover:shadow-[0_0_20px_rgba(59,130,246,0.15)] transition-all duration-500 group/footer">
            <Terminal className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0 group-hover/footer:animate-pulse" />
            <div className="flex flex-col gap-0.5">
              <span className="font-semibold text-neutral-300 group-hover/footer:text-blue-200 transition-colors duration-300">Social Media Autonomous Report</span>
              <span className="text-[10px] text-neutral-500 group-hover/footer:text-neutral-400 transition-colors duration-300">by DEV-Julian • v2.0.0</span>
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 flex flex-col p-8 lg:p-12 z-10 relative">
        <div className="max-w-3xl w-full mx-auto mt-8">

          <div className="mb-12">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 border border-white/10 text-sm font-medium text-neutral-400 mb-6">
              <Activity className="w-4 h-4" />
              Configuration Panel
            </div>
            <h2 className="text-4xl font-semibold text-white mb-4 tracking-tight">
              Target <span className={selectedData.color}>{platform}</span> Profile
            </h2>
            <p className="text-neutral-400 text-lg leading-relaxed">
              Enter the target details below. Ensure your browser profile remains authenticated before initiating the autonomous reporting sequence.
            </p>
          </div>

          <div className="bg-black/40 backdrop-blur-2xl border border-white/10 rounded-2xl p-8 shadow-2xl relative overflow-hidden group">

            <div className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-current to-transparent opacity-50 ${selectedData.color}`}></div>

            <div className="space-y-8">

              <div className="space-y-3">
                <label className="block text-sm font-medium text-neutral-300 ml-1">Target URL or Username</label>
                <div className="relative">
                  <input
                    type="text"
                    value={target}
                    onChange={(e) => setTarget(e.target.value)}
                    disabled={isRunning}
                    placeholder={
                      platform.toLowerCase() === 'twitter'
                        ? "e.g., https://x.com/username or https://twitter.com/username"
                        : platform.toLowerCase() === 'threads'
                          ? "e.g., https://www.threads.net/username"
                          : `e.g., https://www.${platform.toLowerCase()}.com/username`
                    }
                    className={`w-full bg-white/5 border rounded-xl px-5 py-4 text-white placeholder-neutral-600 focus:outline-none focus:ring-2 transition-all disabled:opacity-50
                      ${isUrlValid
                        ? 'border-white/10 focus:ring-blue-500/50 focus:border-blue-500/50'
                        : 'border-red-500/60 focus:ring-red-500/50 focus:border-red-500/50'
                      }`}
                  />
                </div>
                {!isUrlValid && (
                  <p className="text-red-400 text-xs ml-1 mt-1 animate-pulse">
                    Please enter a valid URL for {platform}
                    {platform.toLowerCase() === 'threads'
                      ? " (containing 'threads.net' or 'threads.com')"
                      : platform.toLowerCase() === 'twitter'
                        ? " (containing 'twitter.com' or 'x.com')"
                        : ` (containing '${platform.toLowerCase()}.com')`}
                  </p>
                )}
              </div>

              <div className="space-y-3">
                <label className="block text-sm font-medium text-neutral-300 ml-1">Execution Count</label>
                <div className="flex items-center gap-6">
                  <input
                    type="number"
                    min="1"
                    max="1000"
                    value={count}
                    onChange={(e) => setCount(Number(e.target.value))}
                    disabled={isRunning}
                    className="w-36 bg-white/5 border border-white/10 rounded-xl px-5 py-4 text-white font-mono text-lg focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all disabled:opacity-50"
                  />
                  <span className="text-neutral-400 text-sm">Number of automated reports to execute consecutively</span>
                </div>
              </div>

              <div className="pt-6 flex gap-4">
                <button
                  onClick={handleStart}
                  disabled={!target || !isUrlValid || isRunning}
                  className={`flex-1 relative overflow-hidden flex items-center justify-center gap-3 py-4 rounded-xl font-bold text-white transition-all duration-300 shadow-xl
                    ${(!target || !isUrlValid)
                      ? 'bg-white/5 text-neutral-500 cursor-not-allowed border border-white/5'
                      : isRunning
                        ? `bg-blue-600/25 text-blue-300 border border-blue-500/40 ${isPulsing ? 'brightness-125 scale-[1.015] shadow-blue-500/30 shadow-2xl' : ''}`
                        : 'bg-blue-600 hover:bg-blue-500 hover:shadow-blue-500/25 border border-blue-500 hover:-translate-y-0.5'
                    }`}
                >
                  {isRunning ? (
                    <>
                      <div 
                        className={`absolute left-0 top-0 h-full bg-gradient-to-r from-blue-500/20 to-indigo-500/30 transition-all duration-500 ease-out ${isPulsing ? 'opacity-90 bg-blue-500/30' : 'opacity-70'}`} 
                        style={{ width: `${animatedProgress}%` }}
                      >
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-blue-400/20 to-transparent animate-shimmer"></div>
                      </div>
                      <div className={`w-5 h-5 border-2 border-current border-t-transparent rounded-full animate-spin z-10 transition-transform duration-200 ${isPulsing ? 'scale-110 opacity-100' : 'opacity-70'}`}></div>
                      <span className="z-10 flex items-center gap-2">
                        {status === 'confirming' ? 'Awaiting Login Action' : `Executing Sequence ${Math.round(animatedProgress)}%`}
                      </span>
                    </>
                  ) : progress === 100 ? (
                    <>
                      <CheckCircle2 className="w-5 h-5" />
                      Sequence Complete
                    </>
                  ) : (
                    <>
                      <Play className="w-5 h-5" fill="currentColor" />
                      Launch Automation
                    </>
                  )}
                </button>

                {isRunning && (
                  <button
                    onClick={handleStop}
                    className="px-6 bg-red-950/40 hover:bg-red-900/60 border border-red-500/40 hover:border-red-500 text-red-400 font-bold rounded-xl transition-all flex items-center justify-center gap-2 hover:shadow-lg hover:shadow-red-500/10 active:scale-95 cursor-pointer"
                  >
                    Stop
                  </button>
                )}
              </div>

            </div>
          </div>

          {promptText && (
            <div className="mt-8 p-5 rounded-2xl border border-yellow-500/30 bg-yellow-500/10 backdrop-blur-md flex flex-col md:flex-row items-center justify-between gap-4 animate-pulse">
              <div className="flex items-center gap-3">
                <Shield className="w-6 h-6 text-yellow-400 flex-shrink-0" />
                <div>
                  <div className="font-bold text-white text-sm">Action Required</div>
                  <div className="text-xs text-neutral-300">{promptText}</div>
                </div>
              </div>
              <button
                onClick={handleConfirmLogin}
                className="px-5 py-2.5 bg-yellow-500 hover:bg-yellow-400 text-black font-bold text-xs rounded-xl transition-all shadow-lg shadow-yellow-500/20 active:scale-95 cursor-pointer"
              >
                Confirm Logged In
              </button>
            </div>
          )}

          {/* Terminal Console */}
          <div className="mt-8 bg-[#0d0d0d]/80 border border-white/10 rounded-2xl shadow-2xl overflow-hidden flex flex-col font-mono text-xs">
            <div className="flex items-center justify-between px-6 py-4 bg-white/5 border-b border-white/5">
              <div className="flex items-center gap-3">
                <Terminal className="w-4 h-4 text-blue-400" />
                <span className="text-white font-medium tracking-wide">Live Execution Output</span>
                {isRunning ? (
                  <span className="flex h-2 w-2 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                  </span>
                ) : (
                  <span className="h-2 w-2 rounded-full bg-neutral-600"></span>
                )}
              </div>
              <div className="flex items-center gap-4 text-neutral-400">
                <span className="text-[10px] uppercase tracking-wider">{status}</span>
                {logs.length > 0 && (
                  <button
                    onClick={() => setLogs([])}
                    className="hover:text-white transition-colors cursor-pointer"
                  >
                    Clear Logs
                  </button>
                )}
              </div>
            </div>

            <div className="p-6 h-64 overflow-y-auto space-y-2 flex flex-col bg-black/30">
              {logs.length === 0 ? (
                <div className="text-neutral-600 italic flex items-center justify-center h-full">
                  Waiting for automation to launch...
                </div>
              ) : (
                logs.map((log, idx) => {
                  let levelColor = 'text-neutral-400';
                  if (log.level === 'WARNING') levelColor = 'text-yellow-400';
                  if (log.level === 'ERROR') levelColor = 'text-red-400';
                  if (log.level === 'INFO') levelColor = 'text-blue-400';

                  return (
                    <div key={idx} className="flex items-start gap-3 hover:bg-white/5 py-0.5 px-1 rounded transition-colors">
                      <span className="text-neutral-500 flex-shrink-0">[{log.timestamp}]</span>
                      <span className={`${levelColor} font-bold flex-shrink-0`}>[{log.level}]</span>
                      <span className="text-neutral-300 break-all">{log.message}</span>
                    </div>
                  );
                })
              )}
              <div ref={logsEndRef} />
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
