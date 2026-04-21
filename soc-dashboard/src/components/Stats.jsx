import { motion } from "framer-motion";

export default function Stats({ stats }) {
  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      className="bg-[#1e293b] p-4 rounded-xl shadow-lg"
    >
      <h2 className="text-lg mb-2">📊 Stats</h2>

      <p>Total Logs: {stats.total}</p>
      <p>Attacks: {stats.attacks}</p>
      <p>Blocked: {stats.blocked}</p>
    </motion.div>
  );
}