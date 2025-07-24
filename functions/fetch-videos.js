exports.handler = async (event) => {
  const { platform } = event.queryStringParameters;
  try {
    if (platform === 'youtube') {
      const response = await fetch(`https://www.googleapis.com/youtube/v3/videos?part=snippet&chart=mostPopular&maxResults=10&key=${process.env.YOUTUBE_API_KEY}`);
      const data = await response.json();
      return {
        statusCode: 200,
        body: JSON.stringify(data.items.map(item => ({
          id: item.id,
          title: item.snippet.title,
          thumbnail: item.snippet.thumbnails.medium.url
        })))
      };
    } else if (platform === 'tiktok') {
      const response = await fetch('https://open.tiktokapis.com/v2/video/list/?fields=id,desc,cover_image_url', {
        headers: { 'Authorization': `Bearer ${process.env.TIKTOK_ACCESS_TOKEN}` }
      });
      const data = await response.json();
      return {
        statusCode: 200,
        body: JSON.stringify(data.data.videos.map(video => ({
          id: video.id,
          title: video.desc || 'TikTok video',
          thumbnail: video.cover_image_url
        })))
      };
    }
    return { statusCode: 400, body: 'Invalid platform' };
  } catch (error) {
    return { statusCode: 500, body: JSON.stringify({ error: error.message }) };
  }
};
