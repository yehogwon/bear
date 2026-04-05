from __future__ import annotations

from dataclasses import dataclass

from bear.domain.models import ChannelMessage


@dataclass(slots=True)
class ChannelEnvelope:
    body: str
    channel: str


class LocalWebChannel:
    channel_name = 'local_web'

    def send_message(self, message: str) -> ChannelMessage:
        return ChannelMessage(channel=self.channel_name, direction='outbound', body=message)


class DiscordChannel:
    channel_name = 'discord'

    def send_message(self, message: str) -> ChannelMessage:
        return ChannelMessage(channel=self.channel_name, direction='outbound', body=message)
