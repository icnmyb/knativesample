# knativesample
Kubernetes上でサーバレスを実現するknativeの自分用メモ

k8sにknativeのコンポーネント入れるのは公式チューリアルで頑張る

$ kubectl create secret generic {secret名} --from-file=key.json=<サービスアカウントのパス>
$ kubectl create -f gcp-config.yaml
$ kubectl create -f datastore-kind.yaml
$ kubectl create -f redis_config.yaml
$ kubectl create -f build-bot.yaml
$ kubectl apply -f build.yaml

$ kubectl apply -f cron.yaml
これでcronjobが作成できる