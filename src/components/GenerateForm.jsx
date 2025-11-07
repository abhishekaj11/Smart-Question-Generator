import React, { useState } from "react";

export default function GenerateForm({ setLoading }) {
  const [subjectCode, setSubjectCode] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    setLoading(true);
    setTimeout(() => {
      fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ subcode: subjectCode }),
      }).then(() => setLoading(false));
    }, 4000);
  };

  return (
    <div className="generate-form">
      <h4>Generate Question Paper</h4>
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Enter Subject Code"
          value={subjectCode}
          onChange={(e) => setSubjectCode(e.target.value)}
          required
        />
        <button type="submit" className="btn-green">Generate QP</button>
      </form>
    </div>
  );
}
