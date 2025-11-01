from auth_spt import authenticate_user, get_user_playlists, export_selected_playlists

if __name__ == "__main__":
    sp = authenticate_user()
    user = sp.current_user()
    print(f"Authenticated as: {user['display_name']}\n")
    
    playlists = get_user_playlists(sp)
    print("Your playlists:")
    for idx, pl in enumerate(playlists):
        print(f"{idx}: {pl['name']} ({pl['tracks_total']} tracks)")

    selection = input("\nEnter playlist numbers to export (comma-separated): ")
    selected_indices = [int(x.strip()) for x in selection.split(",") if x.strip().isdigit()]
    selected_ids = [playlists[i]['id'] for i in selected_indices]

    export_selected_playlists(sp, selected_ids)

