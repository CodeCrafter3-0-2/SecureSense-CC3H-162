import { motion } from "framer-motion";

export default function LiveLogs({ logs }) {
  return (
    <div className="h-[500px] overflow-y-auto">
      <h2 className="text-lg mb-3 text-cyan-400">📡 Live Traffic</h2>

      {logs.map((log, i) => {
        const isAttack = log.prediction !== "Normal Traffic";

        return (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className={`p-3 my-2 rounded-lg flex justify-between items-center ${
              isAttack
                ? "bg-red-900/30 border border-red-500/40"
                : "bg-green-900/20 border border-green-500/30"
            }`}
          >
            <div>
              <p className="font-semibold">{log.ip}</p>
              <p className="text-xs text-gray-400">
                {log.prediction} • {log.confidence}
              </p>
            </div>

            <span className="text-xs text-gray-300">
              {log.blocked}
            </span>
          </motion.div>
        );
      })}
    </div>
  );
}