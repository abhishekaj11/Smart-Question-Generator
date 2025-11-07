import React, { useState } from "react";

export default function RuleSelector() {
  const [rules, setRules] = useState({
    one: false,
    two: false,
    five: false,
    twelve: false,
    sixteen: false,
  });

  const toggleRule = (rule) => {
    setRules((prev) => ({ ...prev, [rule]: !prev[rule] }));
  };

  return (
    <div className="rule-selector">
      <h5>Rule-Based Selector</h5>
      <div className="rules">
        {Object.entries(rules).map(([key, value]) => (
          <label key={key}>
            <input
              type="checkbox"
              checked={value}
              onChange={() => toggleRule(key)}
            />
            {key.replace(/^\w/, (c) => c.toUpperCase())} Mark Rule
          </label>
        ))}
      </div>
    </div>
  );
}
