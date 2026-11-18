"""Traditional autoencoder publication counts without a connecting line."""
from review_charts import cli

if __name__ == '__main__':
    cli(default_group='traditional_ae', charts=['year'], year_line=False)
