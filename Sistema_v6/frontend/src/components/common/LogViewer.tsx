import React, { useEffect, useRef, useState } from 'react';
import { Terminal, X, Pause, Play, Trash2, Download } from 'lucide-react';

interface LogViewerProps {
    isOpen: boolean;
    onClose: () => void;
}

export const LogViewer: React.FC<LogViewerProps> = ({ isOpen, onClose }) => {
    const [logs, setLogs] = useState<string[]>([]);
    const [isPaused, setIsPaused] = useState(false);
    const [isConnected, setIsConnected] = useState(false);
    const wsRef = useRef<WebSocket | null>(null);
    const logsEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (isOpen) {
            // Connect to WebSocket
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.hostname}:8000/api/v1/logs/ws`;

            const ws = new WebSocket(wsUrl);
            wsRef.current = ws;

            ws.onopen = () => {
                setIsConnected(true);
                setLogs(prev => [...prev, '--- Conectado al stream de logs ---']);
            };

            ws.onmessage = (event) => {
                if (!isPaused) {
                    setLogs(prev => {
                        const newLogs = [...prev, event.data];
                        // Keep only last 1000 lines to prevent memory issues
                        if (newLogs.length > 1000) {
                            return newLogs.slice(newLogs.length - 1000);
                        }
                        return newLogs;
                    });
                }
            };

            ws.onclose = () => {
                setIsConnected(false);
                setLogs(prev => [...prev, '--- Desconectado del stream ---']);
            };

            ws.onerror = (error) => {
                console.error('WebSocket error:', error);
                setLogs(prev => [...prev, '--- Error de conexión ---']);
            };

            return () => {
                ws.close();
            };
        }
    }, [isOpen]);

    // Auto-scroll to bottom
    useEffect(() => {
        if (!isPaused && logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs, isPaused]);

    const handleClear = () => setLogs([]);
    const handleDownload = () => {
        const blob = new Blob([logs.join('\n')], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `sintaxis-logs-${new Date().toISOString()}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-gray-900 w-full max-w-5xl h-[80vh] rounded-lg shadow-2xl flex flex-col border border-gray-700">
                {/* Header */}
                <div className="flex items-center justify-between px-4 py-3 border-b border-gray-700 bg-gray-800 rounded-t-lg">
                    <div className="flex items-center gap-2 text-gray-100">
                        <Terminal className="w-5 h-5 text-blue-400" />
                        <h2 className="font-semibold">Logs del Sistema</h2>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${isConnected ? 'bg-green-900 text-green-300' : 'bg-red-900 text-red-300'}`}>
                            {isConnected ? 'En vivo' : 'Desconectado'}
                        </span>
                    </div>
                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setIsPaused(!isPaused)}
                            className="p-1.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition-colors"
                            title={isPaused ? "Reanudar" : "Pausar"}
                        >
                            {isPaused ? <Play className="w-4 h-4" /> : <Pause className="w-4 h-4" />}
                        </button>
                        <button
                            onClick={handleClear}
                            className="p-1.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition-colors"
                            title="Limpiar"
                        >
                            <Trash2 className="w-4 h-4" />
                        </button>
                        <button
                            onClick={handleDownload}
                            className="p-1.5 hover:bg-gray-700 rounded text-gray-400 hover:text-white transition-colors"
                            title="Descargar"
                        >
                            <Download className="w-4 h-4" />
                        </button>
                        <button
                            onClick={onClose}
                            className="p-1.5 hover:bg-red-900/50 rounded text-gray-400 hover:text-red-400 transition-colors ml-2"
                        >
                            <X className="w-5 h-5" />
                        </button>
                    </div>
                </div>

                {/* Logs Content */}
                <div className="flex-1 overflow-auto p-4 font-mono text-sm bg-black text-gray-300">
                    {logs.map((log, index) => (
                        <div key={index} className="whitespace-pre-wrap break-words hover:bg-gray-900/50 px-1">
                            {log}
                        </div>
                    ))}
                    <div ref={logsEndRef} />
                </div>
            </div>
        </div>
    );
};
