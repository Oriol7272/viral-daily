const ctx = document.getElementById('video-chart').getContext('2d');
let videoChart;
function updateChart(youtubeCount, tiktokCount) {
    if (videoChart) videoChart.destroy();
    videoChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['YouTube', 'TikTok'],
            datasets: [{
                label: 'Número de videos',
                data: [youtubeCount, tiktokCount],
                backgroundColor: ['#FF0000', '#69C9D0'],
                borderColor: ['#CC0000', '#55A8B0'],
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    title: { display: true, text: 'Cantidad de videos' }
                },
                x: {
                    title: { display: true, text: 'Plataforma' }
                }
            },
            plugins: {
                legend: { display: false },
                title: { display: true, text: 'Videos por plataforma en Viral Daily' }
            }
        }
    });
}

async function fetchYouTubeVideos() {
    try {
        const response = await fetch('/.netlify/functions/fetch-videos?platform=youtube');
        const data = await response.json();
        const videoGrid = document.getElementById('youtube-videos');
        videoGrid.innerHTML = data.map(item => `
            <div class="col-md-4">
                <div class="card video-card">
                    <img src="${item.thumb}" class="card-img-top" alt="Thumbnail">
                    <div class="card-body">
                        <h5 class="card-title">${item.title}</h5>
                        <a href="${item.url}" class="btn btn-primary">View Video</a>
                        <p class="affiliate-link"><a href="https://amzn.to/your-affiliate-link?tag=your-id">Buy related product on Amazon</a></p>
                    </div>
                </div>
            </div>
        `).join('');
        return data.length;
    } catch (error) {
        console.error('Error fetching YouTube videos:', error);
        return 10;
    }
}

async function fetchTikTokVideos() {
    try {
        const response = await fetch('/public/videos.json');
        const data = await response.json();
        const videoGrid = document.getElementById('tiktok-videos');
        videoGrid.innerHTML = data.map(video => `
            <div class="col-md-4">
                <div class="card video-card">
                    <img src="${video.thumb}" class="card-img-top" alt="Thumbnail">
                    <div class="card-body">
                        <h5 class="card-title">${video.title}</h5>
                        <a href="${video.url}" class="btn btn-primary">View Video</a>
                        <p class="affiliate-link"><a href="https://amzn.to/your-affiliate-link?tag=your-id">Buy related product on Amazon</a></p>
                    </div>
                </div>
            </div>
        `).join('');
        return data.length;
    } catch (error) {
        console.error('Error fetching TikTok videos from JSON:', error);
        return 10;
    }
}

function initAdSense() {
    (adsbygoogle = window.adsbygoogle || []).push({});
}

function subscribe() {
    alert('Redirecting to subscription page...');
    window.location.href = 'https://buy.stripe.com/your-checkout-link';
}

function setupFilters() {
    const filterButtons = document.querySelectorAll('.platform-filter');
    const videos = document.querySelectorAll('.video-card');

    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            const platform = button.getAttribute('data-platform');
            videos.forEach(video => {
                video.style.display = platform === 'all' || video.closest('section').id === platform ? 'block' : 'none';
            });
        });
    });
}

function setupSearch() {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) {
        console.error('search-input element not found');
        return;
    }
    const videos = document.querySelectorAll('.video-card');

    searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase();
        videos.forEach(video => {
            const title = video.querySelector('.card-title').textContent.toLowerCase();
            video.style.display = title.includes(query) ? 'block' : 'none';
        });
    });
}

function initSubscription() {
    const subscribeButton = document.querySelector('.subscription-button');
    if (subscribeButton) {
        subscribeButton.addEventListener('click', subscribe);
    }
}

function initPWA() {
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/serviceworker.js').catch(err => {
                console.error('ServiceWorker registration failed:', err);
            });
        });
    }
}

async function init() {
    const youtubeCount = await fetchYouTubeVideos();
    const tiktokCount = await fetchTikTokVideos();
    updateChart(youtubeCount, tiktokCount);
    setupFilters();
    setupSearch();
    initSubscription();
    initAdSense();
    initPWA();
}

init();
