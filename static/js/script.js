document.addEventListener("DOMContentLoaded", () => {
    const generateBtn = document.getElementById("generateBtn");
    const courseCodeInput = document.getElementById("courseCode");
    const paperOutput = document.getElementById("paperOutput");

    generateBtn.addEventListener("click", () => {
        const courseCode = courseCodeInput.value.trim();
        if (!courseCode) return alert("Please enter a course code!");

        fetch("/api/generate-paper", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ courseCode })
        })
        .then(res => res.json())
        .then(data => {
            if (data.error) paperOutput.textContent = "Error: " + data.error;
            else paperOutput.textContent = JSON.stringify(data.paper, null, 2);
        })
        .catch(err => console.error(err));
    });
});
