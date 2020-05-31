import re
import praw
import secrets
from imgurpython import ImgurClient

# ignoredWords = ["w2c"]
# might need this later
taobaoUrls = ["taobao.com"]
taobaoDesktopUrl = "https://item.taobao.com/item.htm?id={id}"

# Use '+' to combine multiple subreddits
subreddits = "OiMvk"

comment_body = "**Retrieved the following links from Imgur:**\n\n{urls}\n\n**********\n\n" \
               "^(I am a bot. Please contact) [^(/u/Yezzos)](https://www.reddit.com/user/Yezzos) ^(for any questions)"


class FRLinkArchiver:
    def __init__(self, bot_name):
        self.reddit = praw.Reddit(bot_name)
        self.imgur = ImgurClient(secrets.imgur_client_id, secrets.imgur_client_secret)
        self.links = []
        self.whitelist = []
        self.set_whitelisted_pages()

    def main(self):
        subreddit = self.reddit.subreddit(subreddits)
        for submission in subreddit.stream.submissions(skip_existing=True):
            print("got a new one!")
            self.process_submission(submission)
            if len(self.links):
                comment = comment_body.format(urls="\n\n".join(self.links))
                print(comment)
                submission.reply(comment)

    def get_imgur_description_urls(self, album_id):
        urls = []
        album_images = self.imgur.get_album_images(album_id)
        for image in album_images:
            urls.extend(self.get_urls_from_body(image.description))
        return urls

    def get_urls_from_body(self, body):
        urls = []
        if body is not None:
            lines = body.splitlines()
            for line in lines:
                for possible_url in line.split('http'):
                    url = self.get_url_from_string('http{url}'.format(url=possible_url))
                    if url:
                        urls.append(url)
        return list(set(urls))

    def get_url_from_string(self, url):
        url = url.replace(" ", "")
        # https://stackoverflow.com/questions/839994/extracting-a-url-in-python
        url = re.search("(?P<url>https?://[^\s]+)", url)
        if url:
            url = url.group("url")
            # Convert any taobao urls
            if any(tbUrl in url for tbUrl in taobaoUrls):
                url = taobaoDesktopUrl.format(id=url.split("id=")[-1].split('&')[0])

            if any(whitelistUrl in url for whitelistUrl in self.whitelist):
                return url

    def set_whitelisted_pages(self):
        whitelist_post = self.reddit.subreddit('FashionReps').wiki['whitelist'].content_md.lower()
        self.whitelist = list(filter(None, whitelist_post.splitlines()[4:]))
        print("Created whitelist:", self.whitelist)

    def process_submission(self, submission):
        if submission.is_self:
            self.process_self_text(submission.selftext)
        else:
            self.process_imgur_url(submission.url)

    def process_self_text(self, selftext):
        for ch in ['[', ']', '(', ')']:
            if ch in selftext:
                selftext = selftext.replace(ch, ' ')

        for url in self.get_urls_from_body(selftext):
            self.process_imgur_url(url)

    def process_imgur_url(self, submission_url):
        if "imgur" in submission_url:
            if "/a/" in submission_url:
                split_val = "a"
            elif "/gallery/" in submission_url:
                split_val = "gallery"
            else:
                return

            split_url = submission_url.split('/')
            album_id = split_url[split_url.index(split_val) + 1].split('#')[0]

            if album_id:
                urls = self.get_imgur_description_urls(album_id)
                self.links.extend(urls)


if __name__ == "__main__":
    la = FRLinkArchiver('FRLinkArchiver')
    la.main()
