https://rubygems.org/gems/aws_s3_website_sync

## AWS S3 Website aws_s3_website_sync

This is a tool to sync a folder from your local dev environment to your S3 Bucket and then invalidate the CloudFront cache.

## How to use

Create a GemFile that installs the gem:

```rb
source 'https://rubygems.org'
ruby '3.2.1'

git source(:github) do |repo_name|
    repo_name = "#{repo_name}/#{repo_name}" unless repo_name.include?("/")
    "https://github.com/#{repo_name}.git"
end

gem 'rake'
gem 'morn', github: 'teacherseat/morn', branch: :main, tag: '1.3.2'
gem 'aws_s3_website_sync', tag: '1.0.1'
gem 'dotenv', groups: [:development, :test]


```
Note: It's good practice to indicate the specific ruby version
Then proceed to run a 'bundle install'

```sh
bundle install
```

Create a `RakeFile` with the following:

```rb
require 'aws_s3_website_sync'
require 'dotenv'

```

