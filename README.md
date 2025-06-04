# Playlist to Spotify Importer

A Python tool to import playlists from various file formats (M3U, TXT, CSV) into your Spotify playlists.

## Features

- Import from multiple file formats: M3U, TXT, CSV
- Search and match tracks on Spotify
- Create new playlists or add to existing ones
- Skip duplicate tracks
- Dry-run mode to preview changes
- Automatic track format detection

## Installation

1. Clone this repository:
   ```bash
   git clone <repository-url>
   cd playlist-into-spotify
   ```

2. Install dependencies using uv:
   ```bash
   uv install
   ```

   Or using pip:
   ```bash
   pip install spotipy
   ```

## Spotify App Setup

Before using this tool, you need to create a Spotify app to get API credentials:

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
2. Click **Create an App**
3. Fill in the app details:
   - **App name**: Choose any name (e.g., "Playlist Importer")
   - **App description**: Brief description of your app
   - **Redirect URI**: `http://127.0.0.1:8000/callback`
4. Accept the terms and click **Create**
5. In your app dashboard, note down:
   - **Client ID**
   - **Client Secret** (click "Show Client Secret")

## Configuration

Set your Spotify credentials as environment variables:

```bash
export SPOTIFY_CLIENT_ID="your_client_id_here"
export SPOTIFY_CLIENT_SECRET="your_client_secret_here"
```

Or create a `.envrc` file (if using direnv):
```bash
export SPOTIFY_CLIENT_ID="your_client_id_here"
export SPOTIFY_CLIENT_SECRET="your_client_secret_here"
```

## Usage

### Basic Usage

```bash
python playlist_to_spotify.py <playlist_file> <spotify_playlist_name>
```

### Examples

Import a CSV playlist to an existing Spotify playlist:
```bash
python playlist_to_spotify.py "Best of Tom Waits.csv" "My Tom Waits Collection"
```

Create a new playlist if it doesn't exist:
```bash
python playlist_to_spotify.py "My Top Rated.csv" "Top Rated Songs" --create-playlist
```

Preview what would be imported (dry run):
```bash
python playlist_to_spotify.py "playlist.m3u" "Test Playlist" --dry-run
```

Skip tracks already in the playlist:
```bash
python playlist_to_spotify.py "playlist.txt" "My Playlist" --skip-duplicates
```

### Command Line Options

- `--create-playlist`: Create the playlist if it doesn't exist
- `--skip-duplicates`: Skip tracks that are already in the target playlist
- `--dry-run`: Show what would be added without actually adding tracks
- `--client-id`: Specify Spotify Client ID (overrides environment variable)
- `--client-secret`: Specify Spotify Client Secret (overrides environment variable)

## Supported File Formats

### CSV Format
CSV files should use semicolon (`;`) as delimiter with columns:
- `title` or `Title`: Song title
- `artist` or `Artist`: Artist name
- Optional: `album`, `isrc`

Example:
```csv
title;artist;album;isrc
Alice;Tom Waits;Alice;usep41718138
November;Tom Waits;The Black Rider;usir19390103
```

### M3U Format
Extended M3U playlists with EXTINF metadata:
```
#EXTM3U
#EXTINF:180,Tom Waits - Alice
/path/to/alice.mp3
#EXTINF:240,Tom Waits - November
/path/to/november.mp3
```

### TXT Format
Plain text with various supported formats:
- `Artist - Title`
- `Title by Artist`
- `Title` (artist will be empty)

Example:
```
Tom Waits - Alice
November by Tom Waits
Ol' 55
```

## First Time Authentication

When you run the tool for the first time, it will:
1. Open your web browser to Spotify's authorization page
2. Ask you to log in and authorize the app
3. Redirect to a local callback URL
4. Automatically extract the authorization code
5. Save the credentials for future use

The authorization token will be cached, so you won't need to re-authorize unless the token expires.

## Troubleshooting

### Common Issues

**"No module named 'spotipy'"**
- Install the required dependency: `uv install` or `pip install spotipy`

**"Spotify credentials required"**
- Make sure you've set the `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` environment variables
- Verify your credentials are correct from your Spotify app dashboard

**"Invalid redirect URI"**
- Ensure your Spotify app's redirect URI is set to `http://127.0.0.1:8000/callback`

**Tracks not found**
- The search uses Spotify's track database - some tracks may not be available
- Try different variations of artist/title if tracks aren't found
- Check for typos in your playlist file

**Authorization issues**
- Delete the `.cache` file created by spotipy and re-authenticate
- Make sure your Spotify app has the correct scopes enabled

## License

This project is open source. See the license file for details.