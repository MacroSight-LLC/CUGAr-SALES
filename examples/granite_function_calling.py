"""Example showing how to call WatsonxProvider deterministically."""

from cuga.providers.watsonx_provider import WatsonxProvider

provider = WatsonxProvider()
print(provider.generate("hello granite", seed=1))
