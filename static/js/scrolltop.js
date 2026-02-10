
//bouton to top
document.addEventListener('DOMContentLoaded', function() {
    const progressPath = document.querySelector('.progress-wrap path');
    const pathLength = progressPath.getTotalLength();
    
    progressPath.style.transition = progressPath.style.webkitTransition = 'none';
    progressPath.style.strokeDasharray = pathLength + ' ' + pathLength;
    progressPath.style.strokeDashoffset = pathLength;
    progressPath.getBoundingClientRect();
    progressPath.style.transition = progressPath.style.webkitTransition = 'stroke-dashoffset 10ms linear';
    
    const updateProgress = function () {
        const scroll = window.pageYOffset;
        const height = document.documentElement.scrollHeight - window.innerHeight;
        const progress = pathLength - (scroll * pathLength / height);
        progressPath.style.strokeDashoffset = progress;
    }
    
    updateProgress();
    window.addEventListener('scroll', updateProgress);
    
    // Apparition du bouton
    const offset = 150;
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > offset) {
            document.querySelector('.progress-wrap').classList.add('active-progress');
        } else {
            document.querySelector('.progress-wrap').classList.remove('active-progress');
        }
    });
    
    // Clic pour remonter
    document.querySelector('.progress-wrap').addEventListener('click', function(event) {
        event.preventDefault();
        window.scrollTo({top: 0, behavior: 'smooth'});
        return false;
    });
});
