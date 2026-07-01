// Lottie Animation Script
document.addEventListener('DOMContentLoaded', function() {
    // Background gradient replaced with CSS, no Lottie needed

    // Animation for login page
    const loginAnimation = document.getElementById('login-animation');
    if (loginAnimation) {
        lottie.loadAnimation({
            container: loginAnimation,
            renderer: 'svg',
            loop: true,
            autoplay: true,
            path: 'https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json' // Medical/health animation
        });
    }

    // Animation for dashboard header
    const dashboardAnimation = document.getElementById('dashboard-animation');
    if (dashboardAnimation) {
        lottie.loadAnimation({
            container: dashboardAnimation,
            renderer: 'svg',
            loop: true,
            autoplay: true,
            path: 'https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json' // Medical/health animation
        });
    }

    // Background analysis animation for dashboard
    const analysisAnimation = document.getElementById('analysis-animation');
    if (analysisAnimation) {
        lottie.loadAnimation({
            container: analysisAnimation,
            renderer: 'svg',
            loop: true,
            autoplay: true,
            path: 'https://assets5.lottiefiles.com/packages/lf20_5njp3vgg.json' // Analysis/data animation
        });
    }

    // Animation for create plan page
    const planAnimation = document.getElementById('plan-animation');
    if (planAnimation) {
        lottie.loadAnimation({
            container: planAnimation,
            renderer: 'svg',
            loop: true,
            autoplay: true,
            path: 'https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json' // Medical/health animation
        });
    }

    // Background health/AI animation for create plan
    const backgroundHealthAnimation = document.getElementById('background-health-animation');
    if (backgroundHealthAnimation) {
        lottie.loadAnimation({
            container: backgroundHealthAnimation,
            renderer: 'svg',
            loop: true,
            autoplay: true,
            path: 'https://assets5.lottiefiles.com/packages/lf20_5njp3vgg.json' // Subtle AI/health background animation
        });
    }

    // Animation for progress page
    const progressAnimation = document.getElementById('progress-animation');
    if (progressAnimation) {
        lottie.loadAnimation({
            container: progressAnimation,
            renderer: 'svg',
            loop: true,
            autoplay: true,
            path: 'https://assets2.lottiefiles.com/packages/lf20_jcikwtux.json' // Medical/health animation
        });
    }
});
