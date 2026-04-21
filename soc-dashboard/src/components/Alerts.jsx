export default function Alerts({ alerts }) {
  return (
    <div className="h-[500px] overflow-y-auto">
      <h2 className="text-lg mb-3 text-red-400">🚨 Critical Alerts</h2>

      {alerts.map((a, i) => (
        <div
          key={i}
          className="bg-red-900/30 border border-red-500/40 p-3 rounded-lg mb-3 shadow-[0_0_15px_rgba(255,0,0,0.3)]"
        >
          <p className="font-semibold">{a.ip}</p>
          <p className="text-sm">{a.prediction}</p>
          <p className="text-xs text-gray-400">
            Risk Score: {a.confidence}
          </p>
        </div>
      ))}
    </div>
  );
}