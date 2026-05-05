function combineOTP() {
  let otp =
    document.getElementById("d1").value +
    document.getElementById("d2").value +
    document.getElementById("d3").value +
    document.getElementById("d4").value +
    document.getElementById("d5").value +
    document.getElementById("d6").value;

  document.getElementById("finalOtp").value = otp;
}

let totalSeconds = 120;
const timer = document.getElementById("countdown");

function startTimer() {
  updateDisplay();
  interval = setInterval(() => {
    if (totalSeconds > 0) {
      totalSeconds--;
      updateDisplay();
    } else {
      clearInterval(interval);
    }
  }, 1000);
}

function updateDisplay() {
  let minutes = Math.floor(totalSeconds / 60);
  let seconds = totalSeconds % 60;
  timer.innerText =
    minutes + ":" + (seconds < 10 ? "0" + seconds : seconds);
}

startTimer();

// auto move cursor
document.querySelectorAll(".otp-inputs input").forEach((input, index, inputs) => {
  input.addEventListener("input", () => {
    if (input.value && index < inputs.length - 1) {
      inputs[index + 1].focus();
    }
  });
});
