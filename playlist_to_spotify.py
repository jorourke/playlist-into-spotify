#!/usr/bin/env python3
"""
Playlist to Spotify Library Importer

Reads playlists from various formats (M3U, TXT, CSV) and adds tracks to your Spotify library.
Requires Spotify API credentials (Client ID and Client Secret).
"""

import argparse
import csv
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

import spotipy
from spotipy.oauth2 import SpotifyOAuth


class PlaylistReader:
    """Handles reading playlists from various file formats."""

    @staticmethod
    def read_m3u(file_path: str) -> List[Dict[str, str]]:
        """Read M3U playlist file and extract track information."""
        tracks = []
        current_track = {}

        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if line.startswith("#EXTINF:"):
                    # Extract track info from EXTINF line
                    # Format: #EXTINF:duration,Artist - Title
                    match = re.search(r"#EXTINF:\d+,(.+)", line)
                    if match:
                        info = match.group(1)
                        if " - " in info:
                            artist, title = info.split(" - ", 1)
                            current_track = {
                                "artist": artist.strip(),
                                "title": title.strip(),
                            }
                        else:
                            current_track = {"artist": "", "title": info.strip()}
                elif line and not line.startswith("#"):
                    # This is a file path/URL, add the track
                    if current_track:
                        tracks.append(current_track)
                        current_track = {}
                    else:
                        # If no EXTINF, try to extract from filename
                        filename = Path(line).stem
                        if " - " in filename:
                            artist, title = filename.split(" - ", 1)
                            tracks.append(
                                {"artist": artist.strip(), "title": title.strip()}
                            )
                        else:
                            tracks.append({"artist": "", "title": filename})

        return tracks

    @staticmethod
    def read_txt(file_path: str) -> List[Dict[str, str]]:
        """Read TXT playlist file with various formats."""
        tracks = []

        with open(file_path, "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()
                if not line:
                    continue

                # Try different formats
                if " - " in line:
                    artist, title = line.split(" - ", 1)
                    tracks.append({"artist": artist.strip(), "title": title.strip()})
                elif " by " in line:
                    title, artist = line.split(" by ", 1)
                    tracks.append({"artist": artist.strip(), "title": title.strip()})
                else:
                    tracks.append({"artist": "", "title": line.strip()})

        return tracks

    @staticmethod
    def read_csv(file_path: str) -> List[Dict[str, str]]:
        """Read CSV playlist file with columns: artist, title."""
        tracks = []

        with open(file_path, "r", encoding="utf-8") as file:
            reader = csv.DictReader(file, delimiter=";")
            for row in reader:
                # Support various column names
                artist = (
                    row.get("artist", "")
                    or row.get("Artist", "")
                    or row.get("ARTIST", "")
                )
                title = (
                    row.get("title", "")
                    or row.get("Title", "")
                    or row.get("TITLE", "")
                    or row.get("track", "")
                    or row.get("Track", "")
                    or row.get("song", "")
                    or row.get("Song", "")
                )

                if title:
                    tracks.append({"artist": artist.strip(), "title": title.strip()})

        return tracks


class SpotifyManager:
    """Handles Spotify API interactions."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str = "http://127.0.0.1:8000/callback",
    ):
        """Initialize Spotify client with OAuth authentication."""
        scope = "playlist-modify-public playlist-modify-private playlist-read-private user-library-read"

        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope,
            )
        )

    def search_track(self, artist: str, title: str) -> Optional[str]:
        """Search for a track and return its Spotify ID."""
        # Build search query
        if artist:
            query = f"track:{title} artist:{artist}"
        else:
            query = f"track:{title}"

        try:
            results = self.sp.search(q=query, type="track", limit=1)
            if results["tracks"]["items"]:
                return results["tracks"]["items"][0]["id"]
        except Exception as e:
            print(f"Error searching for '{title}' by '{artist}': {e}")

        return None

    def find_playlist(self, playlist_name: str) -> Optional[str]:
        """Find a playlist by name and return its ID."""
        try:
            playlists = self.sp.current_user_playlists()
            for playlist in playlists["items"]:
                if playlist["name"].lower() == playlist_name.lower():
                    return playlist["id"]

            # Check if there are more playlists to fetch
            while playlists["next"]:
                playlists = self.sp.next(playlists)
                for playlist in playlists["items"]:
                    if playlist["name"].lower() == playlist_name.lower():
                        return playlist["id"]

            return None
        except Exception as e:
            print(f"Error finding playlist '{playlist_name}': {e}")
            return None

    def create_playlist(
        self, playlist_name: str, description: str = ""
    ) -> Optional[str]:
        """Create a new playlist and return its ID."""
        try:
            user_id = self.sp.current_user()["id"]
            playlist = self.sp.user_playlist_create(
                user_id, playlist_name, public=False, description=description
            )
            return playlist["id"]
        except Exception as e:
            print(f"Error creating playlist '{playlist_name}': {e}")
            return None

    def add_tracks_to_playlist(self, playlist_id: str, track_ids: List[str]) -> bool:
        """Add tracks to a specific playlist."""
        try:
            # Spotify API allows max 100 tracks per request for playlists
            for i in range(0, len(track_ids), 100):
                batch = track_ids[i : i + 100]
                track_uris = [f"spotify:track:{track_id}" for track_id in batch]
                self.sp.playlist_add_items(playlist_id, track_uris)
            return True
        except Exception as e:
            print(f"Error adding tracks to playlist: {e}")
            return False

    def is_track_in_playlist(self, playlist_id: str, track_id: str) -> bool:
        """Check if track is already in the playlist."""
        try:
            tracks = self.sp.playlist_tracks(playlist_id)
            for item in tracks["items"]:
                if item["track"] and item["track"]["id"] == track_id:
                    return True

            # Check if there are more tracks to fetch
            while tracks["next"]:
                tracks = self.sp.next(tracks)
                for item in tracks["items"]:
                    if item["track"] and item["track"]["id"] == track_id:
                        return True

            return False
        except Exception as e:
            print(f"Error checking track in playlist: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Import playlist into Spotify playlist"
    )
    parser.add_argument(
        "playlist_file", help="Path to playlist file (M3U, TXT, or CSV)"
    )
    parser.add_argument(
        "playlist_name", help="Name of the Spotify playlist to add tracks to"
    )
    parser.add_argument(
        "--client-id", help="Spotify Client ID (or set SPOTIFY_CLIENT_ID env var)"
    )
    parser.add_argument(
        "--client-secret",
        help="Spotify Client Secret (or set SPOTIFY_CLIENT_SECRET env var)",
    )
    parser.add_argument(
        "--create-playlist",
        action="store_true",
        help="Create playlist if it doesn't exist",
    )
    parser.add_argument(
        "--skip-duplicates", action="store_true", help="Skip tracks already in playlist"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be added without adding"
    )

    args = parser.parse_args()

    # Get credentials
    client_id = args.client_id or os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = args.client_secret or os.getenv("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        print(
            "Error: Spotify credentials required. Set SPOTIPY_CLIENT_ID and SPOTIPY_CLIENT_SECRET environment variables or use --client-id and --client-secret flags."
        )
        sys.exit(1)

    # Determine file format and read playlist
    file_path = args.playlist_file
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)

    file_ext = Path(file_path).suffix.lower()

    if file_ext == ".m3u":
        tracks = PlaylistReader.read_m3u(file_path)
    elif file_ext == ".txt":
        tracks = PlaylistReader.read_txt(file_path)
    elif file_ext == ".csv":
        tracks = PlaylistReader.read_csv(file_path)
    else:
        print(
            f"Error: Unsupported file format '{file_ext}'. Supported formats: .m3u, .txt, .csv"
        )
        sys.exit(1)

    if not tracks:
        print("No tracks found in playlist file.")
        sys.exit(1)

    print(f"Found {len(tracks)} tracks in playlist.")

    # Initialize Spotify manager
    try:
        spotify = SpotifyManager(client_id, client_secret)
    except Exception as e:
        print(f"Error initializing Spotify connection: {e}")
        sys.exit(1)

    # Find or create the playlist
    playlist_id = spotify.find_playlist(args.playlist_name)
    if not playlist_id:
        if args.create_playlist:
            print(
                f"Playlist '{args.playlist_name}' not found. Creating new playlist..."
            )
            playlist_id = spotify.create_playlist(
                args.playlist_name, f"Imported from {Path(file_path).name}"
            )
            if not playlist_id:
                print("Failed to create playlist.")
                sys.exit(1)
            print(f"✓ Created playlist '{args.playlist_name}'")
        else:
            print(
                f"Error: Playlist '{args.playlist_name}' not found. Use --create-playlist to create it."
            )
            sys.exit(1)
    else:
        print(f"Found playlist '{args.playlist_name}'")

    # Search for tracks and collect IDs
    found_tracks = []
    not_found_tracks = []

    print("Searching for tracks on Spotify...")
    for i, track in enumerate(tracks, 1):
        print(f"[{i}/{len(tracks)}] Searching: {track['artist']} - {track['title']}")

        track_id = spotify.search_track(track["artist"], track["title"])
        if track_id:
            # Check if already in playlist
            if args.skip_duplicates and spotify.is_track_in_playlist(
                playlist_id, track_id
            ):
                print("  → Already in playlist, skipping")
                continue

            found_tracks.append(track_id)
            print("  → Found")
        else:
            not_found_tracks.append(track)
            print("  → Not found")

    # Summary
    print("\nResults:")
    print(f"  Found: {len(found_tracks)} tracks")
    print(f"  Not found: {len(not_found_tracks)} tracks")

    if not_found_tracks:
        print("\nTracks not found:")
        for track in not_found_tracks:
            print(f"  - {track['artist']} - {track['title']}")

    # Add tracks to playlist
    if found_tracks:
        if args.dry_run:
            print(
                f"\nDry run: Would add {len(found_tracks)} tracks to playlist '{args.playlist_name}'."
            )
        else:
            print(
                f"\nAdding {len(found_tracks)} tracks to playlist '{args.playlist_name}'..."
            )
            if spotify.add_tracks_to_playlist(playlist_id, found_tracks):
                print(
                    f"✓ Successfully added tracks to playlist '{args.playlist_name}'!"
                )
            else:
                print("✗ Failed to add tracks to playlist.")
                sys.exit(1)
    else:
        print("\nNo tracks to add.")


if __name__ == "__main__":
    main()
