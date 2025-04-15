const feedparser = require('feedparser-promised');

exports.handler = async (event, context) => {
  try {
    const feeds = [
      'http://rss.cnn.com/rss/cnn_topstories.rss',
      'http://feeds.bbci.co.uk/news/rss.xml',
      'https://www.theguardian.com/world/rss'
    ];
    
    const articles = await Promise.all(
      feeds.map(url => feedparser.parse(url))
      .then(results => results.flat())
      .then(items => items
        .map(item => ({
          title: item.title,
          link: item.link,
          published: item.pubdate,
          summary: item.summary,
          source: item.meta.title
        }))
        .sort((a, b) => new Date(b.published) - new Date(a.published))
        .slice(0, 15)
    );
    
    return {
      statusCode: 200,
      body: JSON.stringify(articles)
    };
  } catch (err) {
    return {
      statusCode: 500,
      body: JSON.stringify({ error: err.message })
    };
  }
};