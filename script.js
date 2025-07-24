// Configuración del gráfico de barras
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

// Función para cargar videos de YouTube
async function fetchYouTubeVideos() {
    try {
        const response = await fetch('/.netlify/functions/fetch-videos?platform=youtube');
        const data = await response.json();
        const videoGrid = document.getElementById('youtube-videos');
        videoGrid.innerHTML = data.map(item => `
            <div class="video" data-platform="youtube">
                <a href="${item.url}">${item.title}</a>
                <img src="${item.thumb}" alt="Thumbnail">
                <p class="affiliate-link"><a href="https://amzn.to/your-affiliate-link?tag=your-id">Buy related product on Amazon</a></p>
            </div>
        `).join('');
        return data.length;
    } catch (error) {
        console.error('Error fetching YouTube videos:', error);
        return 10; // Fallback a videos estáticos
    }
}

// Función para cargar videos de TikTok desde videos.json
async function fetchTikTokVideos() {
    try {
        const response = await fetch('/public/videos.json');
        const data = await response.json();
        const videoGrid = document.getElementById('tiktok-videos');
        videoGrid.innerHTML = data.map(video => `
            <div class="video" data-platform="tiktok">
                <a href="${video.url}">${video.title}</a>
                <img src="${video.thumb}" alt="Thumbnail">
                <p class="affiliate-link"><a href="https://amzn.to/your-affiliate-link?tag=your-id">Buy related product on Amazon</a></p>
            </div>
        `).join('');
        return data.length;
    } catch (error) {
        console.error('Error fetching TikTok videos from JSON:', error);
        return 10; // Fallback a videos estáticos
    }
}

// Función para suscribirse (placeholder para Stripe)
function subscribe() {
    alert('Redirecting to subscription page...');
    window.location.href = 'https://buy.stripe.com/your-checkout-link'; // Replace with your Stripe link
}

// Función para filtrar videos
function setupFilters() {
    const filterButtons = document.querySelectorAll('.platform-filter');
    const videos = document.querySelectorAll('.video');

    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            filterButtons.forEach(btn => btn.classList.remove('active'));
            button.classList.add('active');

            const platform = button.getAttribute('data-platform');
            videos.forEach(video => {
                video.style.display = platform === 'all' || video.getAttribute('data-platform') === platform ? 'block' : 'none';
            });
        });
    });
}

// Función para buscar videos
function setupSearch() {
    const searchInput = document.getElementById('search-input');
    const videos = document.querySelectorAll('.video');

    searchInput.addEventListener('input', () => {
        const query = searchInput.value.toLowerCase();
        videos.forEach(video => {
            const title = video.querySelector('a').textContent.toLowerCase();
            video.style.display = title.includes(query) ? 'block' : 'none';
        });
    });
}

// Función para inicializar la app
async function init() {
    const youtubeCount = await fetchYouTubeVideos();
    const tiktokCount = await fetchTikTokVideos();
    updateChart(youtubeCount, tiktokCount);
    setupFilters();
    setupSearch();
}

// Iniciar la app
init();
