document.addEventListener('DOMContentLoaded', function () {
    console.log('Progress charts script loaded successfully');

    // Get data from global variables passed from Django template
    let progressDistributionData = window.progressDistributionData;
    let lessonFrequencyData = window.lessonFrequencyData;

    console.log('Progress data received:', progressDistributionData);
    console.log('Lesson data received:', lessonFrequencyData);

    if (!progressDistributionData) {
        console.error('Progress distribution data not found');
        document.getElementById('progress-chart-error').textContent = 'Error loading chart data';
        document.getElementById('progress-chart-error').style.display = 'block';
        return;
    }

    if (!lessonFrequencyData) {
        console.error('Lesson frequency data not found');
        document.getElementById('lesson-chart-error').textContent = 'Error loading chart data';
        document.getElementById('lesson-chart-error').style.display = 'block';
        return;
    }

    // Prepare data for Progress Distribution Chart (Pie Chart)
    const progressLabels = Object.keys(progressDistributionData);
    const progressValues = Object.values(progressDistributionData);

    // Prepare data for Lesson Frequency Chart (Bar Chart)
    const lessonLabels = Object.keys(lessonFrequencyData);
    const lessonValues = Object.values(lessonFrequencyData);

    // Create Progress Distribution Pie Chart
    const ctxProgress = document.getElementById('progressDistributionChart').getContext('2d');
    new Chart(ctxProgress, {
        type: 'pie',
        data: {
            labels: progressLabels,
            datasets: [{
                label: 'Progress Distribution',
                data: progressValues,
                backgroundColor: [
                    'rgba(54, 162, 235, 0.7)', // Beginner - Blue
                    'rgba(255, 206, 86, 0.7)', // Intermediate - Yellow
                    'rgba(75, 192, 192, 0.7)'  // Advanced - Green
                ],
                borderColor: [
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                },
                title: {
                    display: false,
                }
            }
        }
    });

    // Create Lesson Frequency Bar Chart
    const ctxLesson = document.getElementById('lessonFrequencyChart').getContext('2d');
    new Chart(ctxLesson, {
        type: 'bar',
        data: {
            labels: lessonLabels,
            datasets: [{
                label: 'Lessons per Day',
                data: lessonValues,
                backgroundColor: 'rgba(54, 162, 235, 0.7)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    precision: 0
                }
            },
            plugins: {
                legend: {
                    display: false,
                },
                title: {
                    display: false,
                }
            }
        }
    });
});
