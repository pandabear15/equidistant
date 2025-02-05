# Developer Documentation

## Source Code
All source code is within the root `equidistant` directory, which can be cloned from the [Github Repo](https://github.com/Equidistant-403/equidistant)

## Directory Layout
### General
The `equidistant/shared` directory holds all documentation (user, developer, and API), and the `equidistant/reports`
directory contains our weekly status reports.

### Frontend
Frontend code is in the `equidistant/frontend/my-app` directory. Upon first time cloning the repo, it will be necessary to run the `npm install` command from the `my-app` directory in order to install the dependencies.

Within the `src` directory you will find some more general Typescript utility files, alongside the application's main `App.tsx` and `index.tsx` files. Files relevant to mocking are contained in the `mocks` subdirectory, and files relevant to specific webpages are in the `Pages` subdirectory.

Test files for unit tests are located directory alongside the files they are testing. For example tests for `LoginPage.tsx` are in the `LoginPage.test.tsx` file in the same directory.

### Backend
Backend code is in the `equidistant/backend` directory. Similar to frontend, you'll have to install the necessary python libraries in order to actually run anything. These include django, BitIO, and requests to name a few but we would recommend trying to run and then seeing what's missing to know what's a required install.

## Command
Guide to some basic commands.

### Frontend
All frontend commands should be run from the `./frontend/my-app` directory.

#### Installing dependencies (MUST USE BEFORE ANY OTHER COMMAND)
`npm install`

#### Starting the app locally
`npm start`

#### Rebuilding Dependencies
`npm rebuild`

#### Generating a Mock Service Worker (1 time execution)
`npx msw init public/ --save`

#### to turn MSW on & off for local development
MSW is by default turned off. This is controlled via an environmental variable. If you wish to change this so the default is on, make a `equidistant/frontend/my-app/.env.development` file and change add a value for `REACT_APP_MOCKS_ENABLED` as true. If you just wish to run the development build once with mocking enabled, run `REACT_APP_MOCKS_ENABLED=true npm start`

#### Linter (Show errors)
`npm run lint`

#### Linter (Fix errors)
add `--fix` to the lint command in `package.json` so it looks like
`eslint --fix --ext .ts,.tsx ./src`

#### to run the suite of all unit and integration tests
`npm test`

#### to run a specific test suite
`npm test <filename>`

#### Adding friends
To test the adding friend / location finding functionality, at this point in time it's best to open the application on two web browsers and have two accounts open that are friends with one another.

## Building
### Frontend
To build the front end, make sure you have installed the dependendencies (`npm install`) and then run `npm run build` from
the `equidistant/frontend/my-app` directory.

### Backend
You will need an API Token that can access a database from bit.io. To do this, you must first create
a Bit.io account and database (which can be done for free - the free tier is very generous). Navigate to the "Connect"
tab and copy this key. Then, add an `.env` file to the root directory, with one line that reads
```
BITIO_API_TOKEN=[YOUR_API_TOKEN_HERE]
```
​
Then, to run the server, navigate to the `equidistant/backend/src/httpserver` directory. From here you can execute the following command
```bash
python manage.py runserver 80
```
Where 80 is the port number, to start the server.

## Testing
### Frontend
To test the front end, make sure you have installed the dependendencies and then run `npm run test` from
the `equidistant/frontend/my-app` directory.

### Backend
All you have to do to run the backend tests is run `pytest` from the `equidistant/backend` directory


### Adding New Tests
#### Frontend
Test files are named after the file they are testing. For example, there are tests for `App.tsx` in the `App.test.tsx` file.
Tests in the files can be written inside of a wrapper function that looks like this.
```javascript
it('test name', () => {
    // your test here
})
```

#### Backend
New test files can be added either to specific files that already exist within the `equidistant/backend/tests` directory, or new files can be created there should the desired test not fit into one of the existing files.
​
Some tests that run directly on the server may require running within Django, in which case tests can be added to the `equidistant/backend/src/httpserver/myapp/test.py` file.

### Live Testing
If you want to test on the live deployment located [here](https://equidistant-403.github.io/equidistant/) you'll have to make two accounts with different addresses such that a location query is possible.

## Building a release
Version number should be updated in the top level `README.md` file, and again in the `frontend/my-app/package.json` file.
Then, once the changes are merged to main, [go here](https://github.com/Equidistant-403/equidistant/releases/new) and create a new release.
Names should follow the standard versioning control, where `x.0.0` indicates the major version number (major changes, backwards compatibility breakage), `0.y.0` indicates that minor version (features, backwards compatible changes), and `0.0.z` indicates a patch version (patches and bug fixes). The description should have a list of all changes, specifically highlighting anything that is not backwards compatible in the case of a major version bump.

For backend, the only tasks that currently are not automated is porting code over to our running instance. We pln on making this an automated task in the future, but currently if you're planning on building you should make sure that the frontend is correctly calling whatever endpoint you've ported the backend to via the `process.env.REACT_APP_BACKEND` environment variable.
Our instance is also using ngrok as a tunnel to provide a public URL to the front end, but this is not necessary to run the backend.
