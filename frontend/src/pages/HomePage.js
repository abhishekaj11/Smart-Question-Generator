import React, { useState, useEffect } from "react";

function HomePage() {
  const [courses, setCourses] = useState([]);
  const [selectedCourse, setSelectedCourse] = useState("");
  const [paper, setPaper] = useState(null);
  const [loading, setLoading] = useState(false);

  // Fetch available courses from Flask backend
  useEffect(() => {
    fetch("/api/courses")
      .then((res) => res.json())
      .then((data) => setCourses(data.courses || []))
      .catch((err) => console.error(err));
  }, []);

  const handleGeneratePaper = async () => {
    if (!selectedCourse) return alert("Please select a course!");
    setLoading(true);
    try {
      const res = await fetch("/api/generate-paper", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ courseCode: selectedCourse }),
      });
      const data = await res.json();
      setPaper(data.paper || {});
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-10">
      <h1 className="text-3xl font-bold text-center mb-6 text-blue-600">
        Smart Question Generator 🎓
      </h1>

      <div className="max-w-lg mx-auto bg-white p-6 rounded-2xl shadow-md">
        <label className="block mb-2 font-semibold">Select Subject:</label>
        <select
          value={selectedCourse}
          onChange={(e) => setSelectedCourse(e.target.value)}
          className="w-full border border-gray-300 p-2 rounded-md mb-4"
        >
          <option value="">-- Select a course --</option>
          {courses.map((c, i) => (
            <option key={i} value={c.courseCode}>
              {c.courseCode} - {c.courseName}
            </option>
          ))}
        </select>

        <button
          onClick={handleGeneratePaper}
          disabled={loading}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg w-full hover:bg-blue-700 transition"
        >
          {loading ? "Generating..." : "Generate Question Paper"}
        </button>
      </div>

      {paper && (
        <div className="mt-10 bg-white p-6 rounded-2xl shadow-md max-w-2xl mx-auto">
          <h2 className="text-xl font-bold mb-3 text-blue-700">
            Generated Paper
          </h2>
          <pre className="text-gray-800 bg-gray-100 p-3 rounded-lg overflow-x-auto">
            {JSON.stringify(paper, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

export default HomePage;
