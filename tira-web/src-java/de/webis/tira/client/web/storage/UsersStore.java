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

	/**
	 * @return Tira's "Users" object
	 * @throws ServletException when Tira's "users" file doesn't exist.
	 */
	public static Users	getUsers() 
	throws ServletException {
		File usersPrototext = new File(Directories.USERS, "users.prototext");
		String prototext;
		Users.Builder ub = Users.newBuilder();
		try {
			prototext = FileUtils.readFileToString(usersPrototext, Charsets.UTF_8.name());
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
	
	public static User getUser(String userName)
	throws ServletException {
		Users us = UsersStore.getUsers();
		User u = null;
		for (User user : us.getUsersList()) {
			if (user.getUserName().equals(userName)) {
				u = user;
				break;
			}
		}
		return u;
	}
	
}
