import React, { useState, useEffect } from "react";
import Navbar from "../components/Navbar";
import GenerateForm from "../components/GenerateForm";
import SubjectTable from "../components/SubjectTable";
import RuleSelector from "../components/RuleSelector";

export default function Dashboard() {
  const [subjects, setSubjects] = useState([]);
  const [loading, setLoading] = useState(false);

  // Fetch subject list from Flask (MongoDB)
  useEffect(() => {
    fetch("/api/subjects")
      .then((res) => res.json())
      .then((data) => setSubjects(data))
      .catch((err) => console.error(err));
  }, []);

  return (
    <div className="dashboard-container">
      <Navbar />
      <div className="main-content">
        <div className="left-panel">
          <GenerateForm setLoading={setLoading} />
          <SubjectTable subjects={subjects} />
        </div>
        <div className="right-panel">
          <RuleSelector />
        </div>
      </div>

      {loading && (
        <div className="loading-overlay">
          <div className="spinner"></div>
          <p>Generating your Question Paper...</p>
        </div>
      )}
    </div>
  );
}
