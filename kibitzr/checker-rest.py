<<<<<<< HEAD

    def fetch(self):
        if self.is_script():
            logger.info("Fetching %r using script",
                        self.conf['name'])
        else:
            logger.info("Fetching %r at %r",
                        self.conf['name'], self.conf['url'])
        try:
            ok, content = self.downloader(self.conf)
        except requests.RequestException as e :
            msg="{} {name} {url}".format(e, **self.conf)
            logger.error(msg)
            ok, content = (False, msg)
        except Exception:
            logger.exception(
                "Exception occured while fetching page"
            )
            ok, content = False, "Exception: %s" % traceback.format_exc()[:60]
        return ok, content

    def downloader_factory(self):
        if self.needs_firefox():
            return firefox_fetcher
        elif self.is_script():
            return fetch_by_script
        else:
            return SessionFetcher(self.conf).fetch

    def is_script(self):
        return all((
            'url' not in self.conf,
            'script' in self.conf,
        ))

    def needs_firefox(self):
        return any(
            self.conf.get(key)
            for key in ('scenario', 'delay')
        )

    def transform(self, ok, content):
        ok, content = self.transform_pipeline(ok, content)
        if content:
            content = content.strip()
        return ok, content

    def transform_error_factory(self):
        error_policy = self.conf.get('error', 'notify')
        if error_policy == 'ignore':
            return self.mute
        elif error_policy == 'notify':
            return self.echo
        else:
            logger.warning("Unknown error policy: %r", error_policy)
            logger.info("Defaulting to 'notify'")
            return self.echo

    @staticmethod
    def echo(content):
        # content will be logged in notifier
        msg="({} (... {} chars) ".format(repr(content)[:50],len(repr(content)))
        logger.debug("Notifying on error %s" % msg )
        return msg

    @staticmethod
    def mute(content):
        if content is not None:
            logger.error("Ignoring error in %s", repr(content)[:60])
        return None

    def create_notifiers(self):
        notifiers_conf = self.conf.get('notify', [])
        if not notifiers_conf:
            logger.warning(
                "No notifications configured for %r",
                self.conf['name'],
            )
        return list(filter(None, [
            self.notifier_factory(notifier_conf)
            for notifier_conf in notifiers_conf
        ]))

    @staticmethod
    def notifier_factory(notifier_conf):
        try:
            key, value = next(iter(notifier_conf.items()))
        except AttributeError:
            key, value = notifier_conf, None
        if key == 'python':
            return functools.partial(post_python, code=value)
        elif key == 'bash':
            return functools.partial(post_bash, code=value)
        elif key == 'mailgun':
            return post_mailgun
        elif key == 'gitter':
            return post_gitter
        elif key == 'slack':
            return SlackSession().post
        elif key == 'smtp':
            return functools.partial(post_smtp, notifier_conf=value)
        else:
            logger.error("Unknown notifier %r", key)

    def notify(self, report, **_kwargs):
        if report:
            logger.debug('Sending report: %r', report)
            for notifier in self.notifiers:
                try:
                    notifier(conf=self.conf, report=report)
                except Exception:
                    logger.exception(
                        "Exception occured during sending notification"
                    )
        else:
            logger.debug('Report is empty, skipping notification')