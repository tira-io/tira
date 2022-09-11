const path = require('path')
const { VueLoaderPlugin } = require('vue-loader')
const BundleTracker = require('webpack-bundle-tracker');

module.exports = (env = {}) => {
  return {

    mode: env.prod ? 'production' : 'development',
    devtool: env.prod ? 'source-map' : 'eval-cheap-module-source-map',
    entry: {
      index: './src/index.ts',
      tiraadmin: './src/tira_admin.ts',
      task: './src/task.ts',
      user: './src/user.ts',
    },
    output: {
      filename: '[name].js',
      path: path.resolve(__dirname, '..', 'static', 'tira', 'dist'),
      publicPath: '/public/tira/dist/'
    },
    watchOptions: {
      ignored: /node_modules/
    },
    module: {
      rules: [
        {
          test: /\.vue$/,
          use: 'vue-loader',
        },
        {
          test: /\.ts$/,
          loader: 'ts-loader',
          options: {
            appendTsSuffixTo: [/\.vue$/],
          }
        },
        {
          test: /\.css$/i,
          use: [
            'style-loader',
            'css-loader'
          ]
        },
      ]
    },
    resolve: {
      extensions: ['.ts', '.js', '.vue', '.json'],
      alias: {
        'vue': 'vue/dist/vue.esm-bundler.js'
      }
    },
    plugins: [
      new VueLoaderPlugin(),
      new BundleTracker({
        path: __dirname,
        filename: 'webpack-stats.json',
      })
    ],
    devServer: {
          headers: {
            "Access-Control-Allow-Origin":"\*"
          },
          host: '0.0.0.0',
          port: 8000,
          allowedHosts: 'all',
//          inline: true,
//          hot: true,
//          stats: "minimal",
//          contentBase: __dirname,
//          overlay: true
    }
  };
}
