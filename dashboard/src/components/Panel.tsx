import { motion } from "framer-motion";
import type { ReactNode } from "react";

export function Panel({
  title,
  sub,
  endpoint,
  delay = 0,
  children,
}: {
  title: string;
  sub: string;
  endpoint: string;
  delay?: number;
  children: ReactNode;
}) {
  return (
    <motion.section
      className="panel"
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      <div className="panel-head">
        <div className="panel-head-row">
          <div className="title">{title}</div>
          <span className="endpoint" title="GoldRush endpoint backing this panel">
            {endpoint}
          </span>
        </div>
        <div className="sub">{sub}</div>
      </div>
      {children}
    </motion.section>
  );
}
