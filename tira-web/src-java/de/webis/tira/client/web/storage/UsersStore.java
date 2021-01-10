package de.webis.tira.client.web.storage;

import java.io.File;
import java.io.IOException;

import javax.servlet.ServletException;

import jgravatar.Gravatar;
import jgravatar.GravatarDefaultImage;
import jgravatar.GravatarRating;

import org.apache.commons.io.FileUtils;

import com.google.common.base.Charsets;
import com.google.protobuf.TextFormat;

import de.webis.tira.client.web.generated.TiraClientWebMessages.User;
import de.webis.tira.client.web.generated.TiraClientWebMessages.Users;

public class UsersStore {

	private final File usersPrototext;
	
	public static UsersStore DEFAULT_USERS_STORE = new UsersStore(new File(Directories.USERS, "users.prototext"));
	
	public static final String USERNAME_WITHOUT_VM = "no-vm-assigned";
	
	private static final String USER_WITHOUT_VM = 			
			"users {\n  userPw: \"mon-existing-password\"\n  userName: \"" + USERNAME_WITHOUT_VM + "\"\n}";
	
	public UsersStore(File usersPrototext) {
		this.usersPrototext = usersPrototext;
	}
	/**
	 * @return Tira's "Users" object
	 * @throws ServletException when Tira's "users" file doesn't exist.
	 */
	private Users getUsers() 
	throws ServletException {
		Users.Builder ub = Users.newBuilder();
		try {
			String prototext = FileUtils.readFileToString(usersPrototext, Charsets.UTF_8.name());
			TextFormat.merge(prototext, ub);
		} 
		catch (IOException e) {
			throw new ServletException(e);
		}
		
		Gravatar g = new Gravatar();
		g.setDefaultImage(GravatarDefaultImage.MM);
		g.setRating(GravatarRating.GENERAL_AUDIENCES);
		g.setSize(16);
		for (User.Builder u : ub.getUsersBuilderList()) {
			if (u.hasEmail()) {
				u.setGravatarUrl(g.getUrl(u.getEmail()));
			}
		}
		
		Users users = ub.build();
		return users;
	}
	
	public User getUserWithNameOrNull(String userName)
	throws ServletException {
		if (USERNAME_WITHOUT_VM.equals(userName)) {
			return userWithoutVM();
		}
		
		Users us = getUsers();
		User u = null;
		for (User user : us.getUsersList()) {
			if (user.getUserName().equals(userName)) {
				u = user;
				break;
			}
		}

		return u;
	}
	
	public static User getUser(String userName)
	throws ServletException {
		return DEFAULT_USERS_STORE.getUserWithNameOrNull(userName);
	}
	
	public static User
	userWithoutVM() {
		try {
			Users.Builder ub = Users.newBuilder();
			TextFormat.merge(USER_WITHOUT_VM, ub);
			
			return ub.build().getUsers(0);
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}
}
