import React from "react";

export default function SubjectTable({ subjects }) {
  return (
    <div className="subject-table">
      <h5>Available Subjects</h5>
      <table>
        <thead>
          <tr>
            <th>Subject Code</th>
            <th>Subject Title</th>
          </tr>
        </thead>
        <tbody>
          {subjects.length > 0 ? (
            subjects.map((sub, idx) => (
              <tr key={idx}>
                <td>{sub.code}</td>
                <td>{sub.title}</td>
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan="2" style={{ textAlign: "center" }}>
                No data found
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
