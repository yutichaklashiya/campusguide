  const starGroup = document.querySelector('.stars');
  const stars = document.querySelectorAll('.stars span');
  const textarea = document.querySelector('textarea');
  const button = document.querySelector('button');

  /*STAR CLICK */
  stars.forEach((star, index) => {
    star.addEventListener('click', () => {
      const rating = index + 1;

      starGroup.classList.remove('red', 'orange', 'green');

      if (rating === 1) {
        starGroup.classList.add('red');
      } else if (rating <= 3) {
        starGroup.classList.add('orange');
      } else {
        starGroup.classList.add('green');
      }

      stars.forEach((s, i) => {
        s.classList.toggle('active', i < rating);
      });

      starGroup.setAttribute('data-rating', rating);


      document.getElementById("ratingInput").value = rating;
    });
  });

  /*SUBMIT */
  button.addEventListener('click', (event) => {
    const rating = starGroup.getAttribute('data-rating');
    const message = textarea.value.trim();

    if (rating === "0" || message === "") {
      event.preventDefault();  // STOP form submit
      alert("Please give your feedback.");
    }
  });