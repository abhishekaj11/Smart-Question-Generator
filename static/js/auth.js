document.addEventListener("DOMContentLoaded", function () {
  const loginForm = document.getElementById("loginForm");
  const registerForm = document.getElementById("registerForm");
  const loginToggle = document.getElementById("loginToggle");
  const registerToggle = document.getElementById("registerToggle");
  const loader = document.getElementById("loader");

  // Show login form by default
  loginForm.classList.add("show");

  // Toggle between login and register
  loginToggle.addEventListener("click", () => {
    loginToggle.classList.add("active");
    registerToggle.classList.remove("active");
    registerForm.classList.add("d-none");
    loginForm.classList.remove("d-none");
    setTimeout(() => {
      registerForm.classList.remove("show");
      loginForm.classList.add("show");
    }, 50);
  });

  registerToggle.addEventListener("click", () => {
    registerToggle.classList.add("active");
    loginToggle.classList.remove("active");
    loginForm.classList.add("d-none");
    registerForm.classList.remove("d-none");
    setTimeout(() => {
      loginForm.classList.remove("show");
      registerForm.classList.add("show");
    }, 50);
  });

  // Handle form submissions with loading animation
  const handleSubmit = (event) => {
    event.preventDefault();
    loader.classList.remove("d-none");
    setTimeout(() => {
      event.target.submit(); // proceed with real POST/GET
    }, 5000); // 5-second animation
  };

  loginForm.addEventListener("submit", handleSubmit);
  registerForm.addEventListener("submit", handleSubmit);
});
