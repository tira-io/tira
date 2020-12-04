package de.webis.tira.client.web.authentication;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;

import org.apache.commons.lang.StringUtils;

import de.webis.tira.client.web.generated.TiraClientWebMessages.User;
import de.webis.tira.client.web.storage.UsersStore;

public class Authenticator {
	
	public static final boolean 
	isSignedIn(HttpServletRequest req)
	throws ServletException {
		return isSignedIn(req, UsersStore.DEFAULT_USERS_STORE);
	}
	
	public static final boolean 
	isSignedIn(HttpServletRequest req, UsersStore usersStore)
	throws ServletException {
		return signedInUser(req, usersStore) != null;
	}

	/**
	 * Returns a Tira user object if an existing username was with the Disraptor user header.
	 * 
	 * @param req The incoming request.
	 * @return a Tira user object.
	 * @throws ServletException
	 */
	public static final User
	signedInUser(HttpServletRequest req)
	throws ServletException {
		return signedInUser(req, UsersStore.DEFAULT_USERS_STORE);
	}
	
	public static final User
	signedInUser(HttpServletRequest req, UsersStore usersStore)
	throws ServletException {
		String userName = req.getHeader("X-Disraptor-User");
		if(userName == null) {
			return null;
		}
		
		String vmName = firstVmGroupOrUserWithoutVM(req);
		User ret = usersStore.getUserWithNameOrNull(vmName);
		
		return ret == null ? usersStore.userWithoutVM() : ret;
	}
	
	private static String firstVmGroupOrUserWithoutVM(HttpServletRequest req) {
		String ret = StringUtils.substringBetween("," + req.getHeader("X-Disraptor-Groups") + ",", ",tira-vm-", ",");
		
		return ret == null ? UsersStore.USERNAME_WITHOUT_VM : ret;
	}
}
