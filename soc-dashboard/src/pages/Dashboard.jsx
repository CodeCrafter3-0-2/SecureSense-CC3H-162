import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import LiveLogs from "../components/LiveLogs";
import Alerts from "../components/Alerts";
import Chatbot from "../components/Chatbot";

const WS = "ws://192.168.16.74:8000/ws/logs";

export default function Dashboard() {
  const [logs, setLogs] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    attacks: 0,
    blocked: 0
  });

  useEffect(() => {
    const ws = new WebSocket(WS);

    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);

      setLogs(prev => [data, ...prev.slice(0, 60)]);

      setStats(prev => ({
        total: prev.total + 1,
        attacks: data.prediction !== "Normal Traffic"
          ? prev.attacks + 1
          : prev.attacks,
        blocked: data.blocked !== "Not Blocked"
          ? prev.blocked + 1
          : prev.blocked
      }));

      if (data.needs_review) {
        setAlerts(prev => [data, ...prev]);
      }
    };

    return () => ws.close();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#020617] via-[#020617] to-[#0f172a] text-white p-6">

      {/* 🔥 HEADER */}
      <motion.div 
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex justify-between items-center mb-6"
      >
        <h1 className="text-3xl font-bold text-cyan-400 tracking-wide">
          🚨 SOC AI Command Center
        </h1>

        <div className="flex gap-4 text-sm">
          <span className="text-green-400 animate-pulse">● LIVE</span>
          <span className="text-gray-400">Realtime Threat Monitoring</span>
        </div>
      </motion.div>

      {/* 🔥 STATS */}
      <div className="grid grid-cols-3 gap-4 mb-6">

        {[
          { label: "Total Logs", value: stats.total, color: "cyan" },
          { label: "Attacks", value: stats.attacks, color: "red" },
          { label: "Blocked", value: stats.blocked, color: "yellow" }
        ].map((s, i) => (
          <motion.div
            key={i}
            whileHover={{ scale: 1.05 }}
            className={`bg-white/5 backdrop-blur-lg border border-${s.color}-500/30 p-5 rounded-xl shadow-lg`}
          >
            <p className="text-gray-400 text-sm">{s.label}</p>
            <h2 className={`text-3xl font-bold text-${s.color}-400`}>
              {s.value}
            </h2>
          </motion.div>
        ))}

      </div>

      {/* 🔥 MAIN GRID */}
      <div className="grid grid-cols-12 gap-4">

        {/* 📡 LIVE TRAFFIC */}
        <motion.div
          className="col-span-8 bg-white/5 backdrop-blur-lg border border-cyan-500/20 rounded-xl p-4 shadow-xl"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <LiveLogs logs={logs} />
        </motion.div>

        {/* 🚨 ALERTS */}
        <motion.div
          className="col-span-4 bg-white/5 backdrop-blur-lg border border-red-500/30 rounded-xl p-4 shadow-xl"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
        >
          <Alerts alerts={alerts} />
        </motion.div>

      </div>

      {/* 🤖 FLOATING CHATBOT */}
      <div className="fixed bottom-6 right-6 w-[350px]">
        <Chatbot />
      </div>

    </div>
  );
}